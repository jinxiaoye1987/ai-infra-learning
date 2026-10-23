"""看 DuckDB 的执行计划：列裁剪和过滤条件是否被“推”进了 Parquet 扫描算子。"""
import duckdb

plan = duckdb.sql("""
    EXPLAIN
    SELECT event, count(*) AS pv
    FROM 'events.parquet'
    WHERE ts >= TIMESTAMP '2026-01-10' AND ts < TIMESTAMP '2026-01-11'
    GROUP BY event
""").fetchall()
print(plan[0][1])
