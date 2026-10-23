"""在第 6 周的 clean/ 基础上，再注入 2,000 条“近似重复”：随机改写约 5% 的词并加一段页脚。"""
import glob

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

rng = np.random.default_rng(42)
df = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob("../w6/clean/*.parquet"))], ignore_index=True)
df = df[["id", "url", "text"]]
src = df.sample(2000, random_state=42)

def perturb(t: str) -> str:
    w = t.split()
    for i in rng.choice(len(w), max(1, len(w) // 20), replace=False):
        w[i] = rng.choice(["data", "the", "new", "great", "info", "more"])
    return " ".join(w) + "\nShare this article on social media."

nd = src.assign(id=src["id"] + "-near", text=src["text"].map(perturb))
out = pd.concat([df, nd], ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)
import os; os.makedirs("input", exist_ok=True)
for i, idx in enumerate(np.array_split(np.arange(len(out)), 8)):
    pq.write_table(pa.Table.from_pandas(out.iloc[idx], preserve_index=False), f"input/part-{i}.parquet")
print(f"输入行数 {len(out)} = 清洗后 {len(df)} + 近似重复 {len(nd)}")
print("其中 id 带 -dup（第 6 周注入的完全重复）:", df["id"].str.endswith("-dup").sum())
