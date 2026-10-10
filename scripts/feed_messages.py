import os
import pandahouse as ph

os.environ["CH_HOST"] = "http://clickhouse.lab.karpov.courses:8123"  # в Jupyter, только для сессии
os.environ["CH_DATABASE"] = "simulator_20260820"
os.environ["CH_USER"] = "student"

from getpass import getpass
os.environ["CH_PASSWORD"] = getpass("Password: ")

connection = {
    "host": os.environ["CH_HOST"],
    "database": os.environ["CH_DATABASE"],   
    "user": os.environ["CH_USER"],
    "password": os.environ["CH_PASSWORD"],
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