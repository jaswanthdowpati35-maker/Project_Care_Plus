import json
import boto3
import pandas as pd
import re
import pyarrow as pa
import pyarrow.parquet as pq
import io
import os  # Added to extract filenames safely

def save_parquet_to_s3(df, bucket, key):
    if df.empty:
        print("⚠️ DataFrame is empty. Skipping S3 upload.")
        return
        
    # Convert DataFrame to Parquet
    table = pa.Table.from_pandas(df, preserve_index=False)
    parquet_buffer = io.BytesIO()
    pq.write_table(table, parquet_buffer)

    # Upload to S3
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket, Key=key, Body=parquet_buffer.getvalue())
    print(f"✅ Parquet saved to s3://{bucket}/{key}")
    

def read_log_from_s3(bucket, key):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket, Key=key)
    log_data = response['Body'].read().decode('utf-8')
    return log_data


def lambda_handler(event, context):
    # Step 1: Read data from the bucket
    record = event['Records'][0]
    bucket_name = record['s3']['bucket']['name']
    input_key = record['s3']['object']['key']

    print(f"📥 Triggered by: s3://{bucket_name}/{input_key}")

    # Step 2: Read log data
    raw_logs = read_log_from_s3(bucket_name, input_key)

    # Split the log entries using the delimiter
    entries = [entry.strip() for entry in raw_logs.split('---') if entry.strip()]

    # Regex pattern to extract data
    log_pattern = re.compile(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<log_level>[A-Za-z0-9_]+)\] '
        r'(?P<component>[^\s]+) - TicketID=(?P<ticket_id>[^\s]+) SessionID=(?P<session_id>[^\s]+)\s*'
        r'IP=(?P<ip>.*?) \| ResponseTime=(?P<response_time>-?\d+)ms \| CPU=(?P<cpu>[\d.]+)% \| EventType=(?P<event_type>.*?) \| Error=(?P<error>\w+)\s*'
        r'UserAgent="(?P<user_agent>.*?)"\s*'
        r'Message="(?P<message>.*?)"\s*'
        r'Debug="(?P<debug>.*?)"\s*'
        r'TraceID=(?P<trace_id>.*)'
    )

    # Extract structured data
    parsed_entries = []
    for entry in entries:
        match = log_pattern.search(entry)
        if match:
            parsed_entries.append(match.groupdict())

    # Create DataFrame (Initialize with expected columns to prevent KeyErrors if file is empty)
    columns = ['timestamp', 'log_level', 'component', 'ticket_id', 'session_id', 'ip', 
               'response_time', 'cpu', 'event_type', 'error', 'user_agent', 'message', 'debug', 'trace_id']
    df = pd.DataFrame(parsed_entries, columns=columns)

    if df.empty or df['response_time'].isna().all():
        print("⚠️ No valid log matches found. Aborting processing.")
        return

    # Data cleaning
    # i) Drop trace_id column
    df = df.drop('trace_id', axis=1, errors='ignore')

    # ii) Safely cast columns to appropriate data types first
    df['response_time'] = pd.to_numeric(df['response_time'], errors='coerce').fillna(0).astype(int)
    df['cpu'] = pd.to_numeric(df['cpu'], errors='coerce').fillna(0.0).astype(float)
    df['error'] = df['error'].str.lower().map({'true': True, 'false': False}).fillna(False)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce').astype('datetime64[ms]')

    # iii) Filter out negative response times
    df = df[df['response_time'] >= 0]

    # iv) Typo-fix in log_level 
    fix_log_level = {'INF0': 'INFO', 'DEBG': 'DEBUG', 'warnING': 'WARNING', 'EROR': 'ERROR'}
    df['log_level'] = df['log_level'].replace(fix_log_level)

    # v) Remove duplicate rows
    df = df.drop_duplicates()

    print(f"📊 Processed DataFrame shape: {df.shape}")
    print(df.head())

    # Save the data (Upload Parquet to S3)
    # FIX: Safely extract just the file name using os.path.basename
    base_file_name = os.path.basename(input_key).replace('.log', '.parquet')
    output_key = f'support-logs/processed/{base_file_name}'
    
    save_parquet_to_s3(df, bucket_name, output_key)
