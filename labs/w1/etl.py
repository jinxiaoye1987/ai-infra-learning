"""把三条典型的 Hive SQL 改写成 pandas。每段上方注释是等价 SQL。"""
import argparse
import resource
import time

import pandas as pd


def timed(label):
    def deco(fn):
        def wrap(*a, **kw):
            t = time.perf_counter()
            out = fn(*a, **kw)
            print(f"[{label}] {time.perf_counter() - t:.3f}s  rows={len(out)}")
            return out
        return wrap
    return deco


@timed("q1 daily pv/uv")
def q1_daily(ev: pd.DataFrame) -> pd.DataFrame:
    # SELECT to_date(ts) AS dt, event, count(*) AS pv, count(DISTINCT user_id) AS uv
    # FROM events GROUP BY to_date(ts), event
    return (ev.assign(dt=ev["ts"].dt.floor("D"))
              .groupby(["dt", "event"], observed=True)
              .agg(pv=("user_id", "size"), uv=("user_id", "nunique"))
              .reset_index())


@timed("q2 gmv by city/level")
def q2_gmv(ev: pd.DataFrame, users: pd.DataFrame) -> pd.DataFrame:
    # SELECT u.city, u.level, sum(e.amount) AS gmv, count(*) AS orders
    # FROM events e JOIN users u ON e.user_id = u.user_id
    # WHERE e.event = 'buy'
    # GROUP BY u.city, u.level ORDER BY gmv DESC
    buy = ev.loc[ev["event"] == "buy", ["user_id", "amount"]]
    return (buy.merge(users, on="user_id", how="inner")
               .groupby(["city", "level"], observed=True)
               .agg(gmv=("amount", "sum"), orders=("amount", "size"))
               .reset_index()
               .sort_values("gmv", ascending=False, ignore_index=True))


@timed("q3 top3 users per day")
def q3_top3(ev: pd.DataFrame) -> pd.DataFrame:
    # SELECT * FROM (
    #   SELECT dt, user_id, cnt,
    #          row_number() OVER (PARTITION BY dt ORDER BY cnt DESC, user_id) AS rn
    #   FROM (SELECT to_date(ts) dt, user_id, count(*) cnt FROM events GROUP BY 1, 2) t
    # ) x WHERE rn <= 3
    daily = (ev.assign(dt=ev["ts"].dt.floor("D"))
               .groupby(["dt", "user_id"]).size().rename("cnt").reset_index())
    daily = daily.sort_values(["dt", "cnt", "user_id"], ascending=[True, False, True])
    daily["rn"] = daily.groupby("dt").cumcount() + 1
    return daily[daily["rn"] <= 3].reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", default="events.parquet")
    ap.add_argument("--users", default="users.parquet")
    args = ap.parse_args()

    t = time.perf_counter()
    ev = pd.read_parquet(args.events)
    users = pd.read_parquet(args.users)
    print(f"[read] {time.perf_counter() - t:.3f}s  events={len(ev):,}  "
          f"内存 {ev.memory_usage(deep=True).sum() / 2**20:.1f} MiB")

    r1, r2, r3 = q1_daily(ev), q2_gmv(ev, users), q3_top3(ev)
    r1.to_parquet("q1_daily.parquet", index=False)
    r2.to_parquet("q2_gmv.parquet", index=False)
    r3.to_parquet("q3_top3.parquet", index=False)
    print(r1.head(4), r2.head(3), r3.head(3), sep="\n\n")
    # Linux 上 ru_maxrss 单位是 KiB；macOS 上是字节（见页面说明）
    print(f"\n总耗时 {time.perf_counter() - t:.2f}s  峰值内存(ru_maxrss) "
          f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.0f} MiB")


if __name__ == "__main__":
    main()
