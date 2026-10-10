**Import Necessary Files**
import pyarrow.parquet as pq
import pandas as pd
**Support Logs**
table = pq.read_table("support_logs_2025-07-01.parquet")
print(table.schema)
df = pd.read_parquet("support_logs_2025-07-01.parquet")
print(df.dtypes)
print(df.shape)
df.head()
**Support Tickets**
table = pq.read_table("run-175395154123-part-block-0-r-00000-snappy.parquet")
print(table.schema)
df = pd.read_parquet("run-175394345142-part-block-0-r-00000-snappy.parquet")
print(df.shape)
df.head()
