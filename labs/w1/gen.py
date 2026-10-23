"""造两张表：事件明细 events.parquet（事实表）+ 用户维表 users.parquet。"""
import argparse
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def make_events(n: int, n_users: int, rng: np.random.Generator) -> pd.DataFrame:
    # 30 天内的随机时间点，排序后模拟“按时间追加写入”的日志表
    start = np.datetime64("2026-01-01T00:00:00")
    offsets = np.sort(rng.integers(0, 30 * 24 * 3600, n))
    event = rng.choice(["view", "click", "cart", "buy"], n, p=[0.75, 0.17, 0.05, 0.03])
    amount = np.where(event == "buy", rng.gamma(2.0, 60.0, n).round(2), 0.0)
    return pd.DataFrame({
        "user_id": rng.integers(0, n_users, n, dtype=np.int64),
        "event": event,
        "ts": start + offsets.astype("timedelta64[s]"),
        "amount": amount,
    })


def make_users(n_users: int, rng: np.random.Generator) -> pd.DataFrame:
    return pd.DataFrame({
        "user_id": np.arange(n_users, dtype=np.int64),
        "city": rng.choice(["北京", "上海", "广州", "深圳", "杭州", "成都"], n_users),
        "level": rng.choice(["L1", "L2", "L3"], n_users, p=[0.6, 0.3, 0.1]),
    })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=1_000_000)
    ap.add_argument("--users", type=int, default=50_000)
    ap.add_argument("--row-group-size", type=int, default=100_000)
    ap.add_argument("--csv", action="store_true", help="同时写一份 CSV 用来比较大小")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)  # 固定种子：每次生成同样的数据，结果可复现
    t = time.perf_counter()
    events = make_events(args.rows, args.users, rng)
    users = make_users(args.users, rng)
    pq.write_table(pa.Table.from_pandas(events, preserve_index=False), "events.parquet",
                   row_group_size=args.row_group_size, compression="zstd")
    users.to_parquet("users.parquet", index=False)
    if args.csv:
        events.to_csv("events.csv", index=False)
    print(events.head())
    print(events.dtypes)
    print(f"events={len(events):,} users={len(users):,} 耗时 {time.perf_counter() - t:.2f}s")


if __name__ == "__main__":
    main()
