"""两个实验：① Python 循环 vs 向量化；② 同一列用不同 dtype 的内存占用。"""
import time

import numpy as np
import pandas as pd

ev = pd.read_parquet("events.parquet")
n = len(ev)

# ① 给 buy 事件打 9 折：逐行循环 vs 向量化
t = time.perf_counter()
out = []
for e, a in zip(ev["event"], ev["amount"]):          # 每一行都在 Python 解释器里走一遍
    out.append(a * 0.9 if e == "buy" else a)
loop_s = time.perf_counter() - t

t = time.perf_counter()
vec = np.where(ev["event"] == "buy", ev["amount"] * 0.9, ev["amount"])   # 循环在 C 里完成
vec_s = time.perf_counter() - t
assert np.allclose(out, vec)
print(f"逐行循环 {loop_s:.3f}s | 向量化 {vec_s:.4f}s | 加速 {loop_s / vec_s:.0f}x")

t = time.perf_counter()
ev.apply(lambda r: r["amount"] * 0.9 if r["event"] == "buy" else r["amount"], axis=1)
print(f"df.apply(axis=1) {time.perf_counter() - t:.3f}s  ← 看起来像向量化，其实仍是逐行")

# ② 同一列 event（4 种取值、100 万行）的三种存法
for name, s in {
    "object（Python 字符串对象）": ev["event"].astype(object),
    "str（pandas 3 默认，Arrow 存储）": ev["event"],
    "category（字典编码）": ev["event"].astype("category"),
}.items():
    print(f"{name:32s} {s.memory_usage(deep=True) / 2**20:6.2f} MiB")
print(f"int64 列 user_id                 {ev['user_id'].memory_usage(deep=True) / 2**20:6.2f} MiB"
      f"  (= {n:,} 行 × 8 字节)")
