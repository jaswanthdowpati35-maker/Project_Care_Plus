import re
import pandas as pd
import io
with open("support_logs_2025-07-01.log", encoding='utf-8') as f:
    content = f.read()
len(content)
entries = [entry.strip() for entry in content.split("---") if entry.strip()]
entries[0]
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
        
parsed_entries[0]      
df = pd.DataFrame(parsed_entries)
df.head(3)
df = df.drop("trace_id", axis=1)
df.head(2)
df.info()
df = df.astype({
    "response_time": "int",
    "cpu": "float"
})
df.info()
df['error'] = df['error'].str.lower().map({'true': True, 'false': False})
df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce').astype('datetime64[ms]')
df.info()
df.describe()
df = df[df.response_time>=0]
df.describe()
df["log_level"].value_counts()
fix_log_level = {'INF0': 'INFO', 'DEBG': 'DEBUG', 'warnING': 'WARNING', 'EROR': 'ERROR'}
df['log_level'] = df['log_level'].replace(fix_log_level)
    
df.log_level.value_counts()
df[df.duplicated()]
df = df.drop_duplicates()
df[df.duplicated()]
df.shape
