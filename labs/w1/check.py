"""对数：用 DuckDB 直接对 Parquet 跑原始 SQL，与 pandas 结果逐行比对。"""
import duckdb
import pandas as pd
from pandas.testing import assert_frame_equal

SQL = {
    "q1_daily": """
        SELECT date_trunc('day', ts) AS dt, event, count(*) AS pv, count(DISTINCT user_id) AS uv
        FROM 'events.parquet' GROUP BY 1, 2""",
    "q2_gmv": """
        SELECT u.city, u.level, sum(e.amount) AS gmv, count(*) AS orders
        FROM 'events.parquet' e JOIN 'users.parquet' u USING (user_id)
        WHERE e.event = 'buy' GROUP BY 1, 2""",
    "q3_top3": """
        SELECT * FROM (
          SELECT dt, user_id, cnt,
                 row_number() OVER (PARTITION BY dt ORDER BY cnt DESC, user_id) AS rn
          FROM (SELECT date_trunc('day', ts) AS dt, user_id, count(*) AS cnt
                FROM 'events.parquet' GROUP BY 1, 2)
        ) WHERE rn <= 3""",
}

for name, sql in SQL.items():
    want = duckdb.sql(sql).df()
    got = pd.read_parquet(f"{name}.parquet")
    keys = list(got.columns[:2])
    norm = lambda d: d.astype({c: "int64" for c in d.columns if d[c].dtype.kind in "iu"}) \
                      .sort_values(keys, ignore_index=True)
    # 浮点求和顺序不同会有极小误差，所以用 rtol 而不是精确相等
    assert_frame_equal(norm(got), norm(want), check_dtype=False, rtol=1e-9)
    print(f"{name}: OK ({len(got)} 行一致)")
