import json
import boto3
import pandas as pd
from io import StringIO
import re
import pyarrow as pa
import pyarrow.parquet as pq
import io

def save_parquet_to_s3(df, bucket, key):
    # Convert DataFrame to Parquet
    table = pa.Table.from_pandas(df, preserve_index=False)
    
    # Create a buffer to hold the Parquet data
    parquet_buffer = io.BytesIO()
    pq.write_table(table, parquet_buffer)

    # Initialize S3 client and upload the Parquet file
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket, Key=key, Body=parquet_buffer.getvalue())
    print(f"✅ Parquet saved to s3://{bucket}/{key}")
    

def read_log_from_s3(bucket, key):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket, Key=key)
    log_data = response['Body'].read().decode('utf-8')
    return log_data


def lambda_handler(event, context):
    # 1: read data from the bucket
    bucket_name = 'careplus-data'
    input_key = 'support-logs/raw/support_logs_2025-07-01.log'

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

    # Create DataFrame
    df = pd.DataFrame(parsed_entries)

    # Data cleaning
    # i) Drop trace_id column
    df = df.drop('trace_id', axis=1)

    # ii) Remove Negative response time
    df = df[df['response_time'].astype(int) >= 0]

    # iii) typo-fix in log_level 
    fix_log_level = {'INF0': 'INFO', 'DEBG': 'DEBUG', 'warnING': 'WARNING', 'EROR': 'ERROR'}
    df['log_level'] = df['log_level'].replace(fix_log_level)

    # iv) Remove duplicate rows
    df = df.drop_duplicates()

    # v) Change to appropriate data types (response_time, cpu, timestamp, error)
    df['response_time'] = df['response_time'].astype(int)
    df['cpu'] = df['cpu'].astype(float)
    df['error'] = df['error'].str.lower().map({'true': True, 'false': False})

    # timestamp conversion
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce').astype('datetime64[ms]')
    print(df.shape)
    print(df.head())

    # Save the data (Upload Parquet to S3)
    output_key = 'support-logs/processed/support_logs_2025-07-01.parquet'
    save_parquet_to_s3(df, bucket_name, output_key)
