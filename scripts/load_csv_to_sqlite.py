import sqlite3
import pandas as pd

DB = "/app/superset_home/portfolio.db"
TABLES = (
    "dau_segments",
    "msg_activity",
    "retention",
    "ads_profile",
    "weekly_audience",
)

with sqlite3.connect(DB) as con:
    for name in TABLES:
        df = pd.read_csv(f"/tmp/data/{name}.csv")

        if "dt" in df.columns:
            df["dt"] = pd.to_datetime(df["dt"], errors="coerce")

        df.to_sql(name, con, index=False, if_exists="replace")
        print(f"{name}: {len(df)} rows")
