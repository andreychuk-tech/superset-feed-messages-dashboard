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

q_retention = f"""
SELECT
    toString(cohort_dt) AS cohort,
    w AS week_life,
    source,
    segment,
    {AGE_GROUP} AS age_group,
    {GENDER} AS gender,
    os,
    if(country_raw IN (
           SELECT country
           FROM (
               SELECT coalesce(country, 'unknown') AS country, uniq(user_id) AS u
               FROM simulator_20260820.feed_actions
               GROUP BY country
               ORDER BY u DESC
               LIMIT 5
           )
       ), country_raw, 'other') AS country,
    COUNT() AS cohort_size,
    countIf(arrayExists(x -> intDiv(dateDiff('day', start_day, x), 7) = w, days)) AS users
FROM (
    SELECT
        user_id,
        MIN(dt) AS start_day,
        toMonday(MIN(dt)) AS cohort_dt,
        argMin(source_day, dt) AS source,
        argMin(segment_day, dt) AS segment,
        MAX(age_d) AS age,
        MAX(gender_d) AS gender,
        any(os_d) AS os,
        any(country_d) AS country_raw,
        groupUniqArray(dt) AS days
    FROM (
        SELECT
            user_id, dt,
            argMin(source, time) AS source_day,
            MAX(age) AS age_d,
            MAX(gender) AS gender_d,
            any(os) AS os_d,
            any(coalesce(country, 'unknown')) AS country_d,
            CASE
                WHEN MAX(is_feed) = 1 AND MAX(is_msg) = 1 THEN 'both'
                WHEN MAX(is_feed) = 1 THEN 'feed_only'
                ELSE 'msg_only'
            END AS segment_day
        FROM (
            SELECT user_id, time, CAST(time AS DATE) AS dt, source, age, gender, os, country,
                   1 AS is_feed, 0 AS is_msg
            FROM simulator_20260820.feed_actions
            UNION ALL
            SELECT user_id, time, CAST(time AS DATE) AS dt, source, age, gender, os, country,
                   0 AS is_feed, 1 AS is_msg
            FROM simulator_20260820.message_actions
        )
        GROUP BY user_id, dt
    )
    GROUP BY user_id
)
ARRAY JOIN range(5) AS w
WHERE addDays(cohort_dt, 12 + 7 * w)
      <= (SELECT MAX(CAST(time AS DATE)) FROM simulator_20260820.feed_actions)
  AND cohort_dt >= toDate('2026-07-06')
GROUP BY cohort_dt, w, source, segment, age_group, gender, os, country
ORDER BY cohort, source, segment, age_group, gender, os, country, week_life
"""
q_ads_profile = f"""
SELECT
    segment,
    os,
    country,
    {AGE_GROUP} AS age_group,
    {GENDER} AS gender,
    COUNT() AS users
FROM (
    SELECT
        user_id,
        CASE
            WHEN MAX(is_feed) = 1 AND MAX(is_msg) = 1 THEN 'both'
            WHEN MAX(is_feed) = 1 THEN 'feed_only'
            ELSE 'msg_only'
        END AS segment,
        argMin(source, time) AS source,
        MAX(age) AS age,
        MAX(gender) AS gender,
        any(os) AS os,
        any(coalesce(country, 'unknown')) AS country
    FROM (
        SELECT user_id, time, source, age, gender, os, country, 1 AS is_feed, 0 AS is_msg
        FROM simulator_20260820.feed_actions
        UNION ALL
        SELECT user_id, time, source, age, gender, os, country, 0 AS is_feed, 1 AS is_msg
        FROM simulator_20260820.message_actions
    )
    GROUP BY user_id
)
WHERE source = 'ads'
GROUP BY segment, os, country, age_group, gender
ORDER BY segment, os, country, age_group, gender
"""
q_weekly = '''
SELECT metric, week, users
FROM (
    -- 1. Активные на неделе
    SELECT 'active' AS metric, toStartOfWeek(toDate(time), 1) AS week,
           toInt64(count(DISTINCT user_id)) AS users
    FROM simulator_20260820.feed_actions
    GROUP BY week

    UNION ALL

    -- 2. Новые: первая активность на этой неделе
    SELECT 'new', toStartOfWeek(toDate(min_time), 1) AS week,
           toInt64(count(DISTINCT user_id))
    FROM (
        SELECT user_id, min(time) AS min_time
        FROM simulator_20260820.feed_actions
        GROUP BY user_id
    )
    GROUP BY week

    UNION ALL

    -- 3. Retained: активные и на W, и на W-1
    SELECT 'retained', a.week, toInt64(count(DISTINCT a.user_id))
    FROM (
        SELECT DISTINCT user_id, toStartOfWeek(toDate(time), 1) AS week
        FROM simulator_20260820.feed_actions
    ) a
    INNER JOIN (
        SELECT DISTINCT user_id, toStartOfWeek(toDate(time), 1) AS week
        FROM simulator_20260820.feed_actions
    ) p ON a.user_id = p.user_id AND p.week = a.week - 7
    GROUP BY a.week

    UNION ALL

    -- 4. Gone: были активны на W-1, на W не пришли (знак минус для графика)
    SELECT 'gone', p.next_week AS week, -toInt64(count(DISTINCT p.user_id))
    FROM (
        SELECT DISTINCT user_id,
               addDays(toStartOfWeek(toDate(time), 1), 7) AS next_week
        FROM simulator_20260820.feed_actions
    ) p
    LEFT ANTI JOIN (
        SELECT DISTINCT user_id, toStartOfWeek(toDate(time), 1) AS a_week
        FROM simulator_20260820.feed_actions
    ) a ON p.user_id = a.user_id AND p.next_week = a.a_week
    GROUP BY week
)
WHERE week >= toDate('2026-07-06')
  AND addDays(week, 6) <= (SELECT max(toDate(time)) FROM simulator_20260820.feed_actions)
ORDER BY week, metric
'''

os.makedirs("data", exist_ok=True)
for name, q in [
    ("dau_segments", q_segments),
    ("msg_activity", q_messages),
    ("retention", q_retention),
    ("ads_profile", q_ads_profile),
    ("weekly_audience", q_weekly),
]:
    df = ph.read_clickhouse(q, connection=connection)
    df.to_csv(f"data/{name}.csv", index=False)
    print(name, df.shape)