# %%
import time
import duckdb
import numpy as np
import pandas as pd
# %%
conn = duckdb.connect()
# %%
cur_time = time.time()
df = conn.execute("""
    SELECT * 
    FROM read_csv_auto('*.csv', header = True)
""").df()
print(time.time() - cur_time)
print(df)
# %%
conn.register("df_view", df)
conn.execute("DESCRIBE df_view").df()
# %%
conn.execute("SELECT COUNT(*) FROM df_view").df()
# %%
df.isnull().sum()
# %%
conn.execute("""
CREATE OR REPLACE TABLE applicants AS
    SELECT
        name,
        location,
        email,
        phone,
        profile_link
    FROM df
""")
# %%
conn.execute("FROM applicants").df()
# %%
conn.execute("COPY applicants TO 'applicants.parquet' (FORMAT 'parquet')")