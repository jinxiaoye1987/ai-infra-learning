"""Ray Data 版去重：① 精确去重（文本哈希）② MinHash + LSH 近似去重（band 分桶 + 连通分量）。"""
import argparse
import hashlib
import re
import time

import numpy as np
import pandas as pd
import ray
from datasketch import MinHash

ap = argparse.ArgumentParser()
ap.add_argument("--cpus", type=int, default=4)
ap.add_argument("--bands", type=int, default=16)
ap.add_argument("--rows", type=int, default=8)
ap.add_argument("--bucket", choices=["ray", "driver"], default="driver")
a = ap.parse_args()
NUM_PERM = a.bands * a.rows
ray.init(num_cpus=a.cpus, include_dashboard=False, log_to_driver=False)
ray.data.DataContext.get_current().enable_progress_bars = False

def shingles(text, n=5):
    w = re.findall(r"\w+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(max(1, len(w) - n + 1))}

def add_hash(df: pd.DataFrame) -> pd.DataFrame:
    df["h"] = [hashlib.md5(t.encode()).hexdigest() for t in df["text"]]
    return df

class Signer:                                      # 类 UDF：每个 Actor 只做一次初始化
    def __init__(self):
        self.num_perm = NUM_PERM
    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        sigs = MinHash.bulk([[s.encode() for s in shingles(t)] for t in df["text"]],
                            num_perm=self.num_perm, seed=1)     # 同一 seed → 所有 Actor 用同一组哈希函数
        rows = []
        for doc_id, m in zip(df["id"], sigs):
            hv = m.hashvalues
            for b in range(a.bands):               # 每个 band 一行：(band 号, band 内 r 个哈希值的摘要, 文档 id)
                key = hashlib.md5(hv[b * a.rows:(b + 1) * a.rows].tobytes()).hexdigest()[:16]
                rows.append((b, key, doc_id))
        return pd.DataFrame(rows, columns=["band", "key", "id"])

t0 = time.time()
ds = ray.data.read_parquet("input")
n_in = ds.count()

# ① 精确去重：同一哈希只保留 id 最小的一条
hashed = ds.map_batches(add_hash, batch_format="pandas").materialize()
keep = hashed.groupby("h").map_groups(lambda g: g.sort_values("id").head(1), batch_format="pandas")
exact = keep.drop_columns(["h"]).materialize()
n_exact = exact.count()
t1 = time.time()
print(f"输入 {n_in} 行 → 精确去重后 {n_exact} 行（去掉 {n_in - n_exact}），{t1 - t0:.1f}s")

# ② MinHash 签名 + LSH 分桶
bands = exact.map_batches(Signer, batch_format="pandas", compute=ray.data.ActorPoolStrategy(size=a.cpus))
if a.bucket == "ray":       # 写法 A：分桶也交给 Ray（groupby + map_groups，每个桶调用一次 Python 函数）
    buckets = bands.groupby(["band", "key"]).map_groups(
        lambda g: g if len(g) > 1 else g.iloc[0:0], batch_format="pandas")   # 只保留有碰撞的桶
    coll = buckets.to_pandas()
else:                      # 写法 B：签名在 Ray 上并行算，band 表（每文档 b 行、很窄）拉回 Driver 用 pandas 向量化分桶
    bt = bands.to_pandas()
    coll = bt[bt.duplicated(["band", "key"], keep=False)]
t2 = time.time()

# ③ 连通分量（Driver 上 union-find；碰撞边很少，可以放在单机）
parent = {}
def find(x):
    while parent.setdefault(x, x) != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x
for _, g in coll.groupby(["band", "key"]):
    ids = sorted(g["id"])
    for o in ids[1:]:
        ra, rb = find(ids[0]), find(o)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
groups = {}
for x in parent:
    groups.setdefault(find(x), []).append(x)
drop = {x for root, mem in groups.items() for x in mem if x != root}
n_final = n_exact - len(drop)
print(f"MinHash(b={a.bands},r={a.rows},num_perm={NUM_PERM}) 碰撞行 {len(coll)}，重复簇 {len(groups)}，"
      f"删除 {len(drop)} → 最终 {n_final} 行，{t2 - t1:.1f}s（签名+分桶，分桶方式={a.bucket}）")
near = sum(x.endswith("-near") for x in drop)
print(f"删除的行中 -near 结尾 {near} 条（共注入 2000）；其他 {len(drop) - near} 条")
print(f"总用时 {time.time() - t0:.1f}s")
