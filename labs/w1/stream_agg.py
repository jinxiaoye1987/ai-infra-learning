"""流式（分批）聚合：内存里一次只放一个 batch，像 MapReduce 的 map + combiner + reduce。"""
import resource
from collections import defaultdict

import pandas as pd
import pyarrow.parquet as pq

pf = pq.ParquetFile("events.parquet")
pv = defaultdict(int)          # 可加（additive）指标：分批求和即可合并
uv_sets = defaultdict(set)     # 去重计数不可加：必须保留明细（或用 HyperLogLog 近似）
uv_wrong = defaultdict(int)    # 错误示范：把每批的 UV 直接相加

for i, batch in enumerate(pf.iter_batches(batch_size=200_000, columns=["user_id", "event", "ts"])):
    df = batch.to_pandas()
    df["dt"] = df["ts"].dt.floor("D")
    g = df.groupby(["dt", "event"])["user_id"]
    for k, v in g.size().items():
        pv[k] += v
    for k, v in g.nunique().items():
        uv_wrong[k] += v
    for k, ids in g.unique().items():
        uv_sets[k].update(ids)
    print(f"batch {i}: {len(df):,} 行")

full = pd.read_parquet("q1_daily.parquet").set_index(["dt", "event"])
pv_ok = all(pv[k] == full.loc[k, "pv"] for k in full.index)
uv_ok = all(len(uv_sets[k]) == full.loc[k, "uv"] for k in full.index)
bad = sum(uv_wrong[k] != full.loc[k, "uv"] for k in full.index)
print(f"PV 与全量结果一致: {pv_ok}")
print(f"UV(集合合并) 与全量结果一致: {uv_ok}")
print(f"UV(每批相加) 出错的分组数: {bad} / {len(full)}")
print(f"峰值内存(ru_maxrss) {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.0f} MiB")
