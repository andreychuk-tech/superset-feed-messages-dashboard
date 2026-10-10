import sqlite3
import pandas as pd

DB = "/app/superset_home/portfolio.db"
con = sqlite3.connect(DB)
for name in ("dau_segments", "msg_activity"):
    df = pd.read_csv(f"/tmp/data/{name}.csv", parse_dates=["dt"])
    df.to_sql(name, con, index=False, if_exists="replace")
    print(name, len(df))
con.close()