import os
import pandahouse as ph
from getpass import getpass

def get_setting(name, secret=False):
    value = os.environ.get(name)
    if not value:
        value = getpass(f"{name}: ") if secret else input(f"{name}: ")
    return value

connection = {
    "host": get_setting("CH_HOST"),         # например, http://<хост>:8123
    "database": "simulator_20260820",
    "user": get_setting("CH_USER"),
    "password": get_setting("CH_PASSWORD", secret=True),
}

AGE_GROUP = """
CASE
    WHEN age IS NULL THEN 'unknown'
    WHEN age < 18 THEN '1. <18'
    WHEN age BETWEEN 18 AND 24 THEN '2. 18-24'
    WHEN age BETWEEN 25 AND 34 THEN '3. 25-34'
    WHEN age BETWEEN 35 AND 44 THEN '4. 35-44'
    ELSE '5. 45+'
END
"""
GENDER = "CASE gender WHEN 1 THEN 'male' WHEN 0 THEN 'female' ELSE 'unknown' END"

q_segments = f"""
SELECT dt, segment, {AGE_GROUP} AS age_group, {GENDER} AS gender, city,
       COUNT(DISTINCT user_id) AS dau
FROM (
    SELECT user_id, dt,
           MAX(age) AS age, MAX(gender) AS gender, MAX(city) AS city,
           CASE
               WHEN MAX(is_feed) = 1 AND MAX(is_msg) = 1 THEN 'both'
               WHEN MAX(is_feed) = 1 THEN 'feed_only'
               ELSE 'msg_only'
           END AS segment
    FROM (
        SELECT user_id, CAST(time AS DATE) AS dt, age, gender,
               coalesce(city, 'unknown') AS city, 1 AS is_feed, 0 AS is_msg
        FROM simulator_20260820.feed_actions
        UNION ALL
        SELECT user_id, CAST(time AS DATE) AS dt, age, gender,
               coalesce(city, 'unknown') AS city, 0 AS is_feed, 1 AS is_msg
        FROM simulator_20260820.message_actions
    ) u
    GROUP BY user_id, dt
) c
GROUP BY dt, segment, age_group, gender, city
"""

q_messages = f"""
SELECT dt, {AGE_GROUP} AS age_group, {GENDER} AS gender, city,
       COUNT(*) AS messages, COUNT(DISTINCT user_id) AS senders
FROM (
    SELECT user_id, CAST(time AS DATE) AS dt, age, gender,
           coalesce(city, 'unknown') AS city
    FROM simulator_20260820.message_actions
) m
GROUP BY dt, age_group, gender, city
"""

os.makedirs("data", exist_ok=True)
for name, q in [("dau_segments", q_segments), ("msg_activity", q_messages)]:
    df = ph.read_clickhouse(q, connection=connection)
    df.to_csv(f"data/{name}.csv", index=False)
    print(name, df.shape)