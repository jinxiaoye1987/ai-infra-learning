"""给干净的 FineWeb 样本“加脏”：模拟爬虫原始数据里常见的问题，方便观察每条清洗规则的效果。"""
import glob

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

rng = np.random.default_rng(7)
df = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob("raw/*.parquet"))], ignore_index=True)
n = len(df)


def pick(frac):
    return rng.choice(n, int(n * frac), replace=False)


df["text"] = df["text"].astype(object)
for i in pick(0.03):                                   # ① HTML 残留
    df.at[i, "text"] = "<div class='nav'><a href='/'>Home</a></div>\n" + df.at[i, "text"] + "\n<script>var x=1;</script>"
for i in pick(0.03):                                   # ② 过短的垃圾页
    df.at[i, "text"] = rng.choice(["Click here to subscribe!", "404 Not Found", "Loading...", "Accept cookies"])
for i in pick(0.02):                                   # ③ 符号/数字堆砌
    df.at[i, "text"] = " ".join(rng.choice(["#", "$$", "|", "---", "1234", "@@", "..."], 300))
for i in pick(0.02):                                   # ④ 非英文（中文）页面
    df.at[i, "text"] = "这是一段用于测试语言过滤的中文网页内容，" * 20
for i in pick(0.02):                                   # ⑤ 大量重复行（模板页）
    df.at[i, "text"] = "\n".join(["Copyright 2024 All rights reserved. Terms | Privacy"] * 40)
dups = df.iloc[pick(0.05)].copy()                      # ⑥ 5% 完全重复的文档（换个 id）
dups["id"] = dups["id"] + "-dup"
df = pd.concat([df, dups], ignore_index=True).sample(frac=1, random_state=7).reset_index(drop=True)

df["text"] = df["text"].astype(str)
for i, idx in enumerate(np.array_split(np.arange(len(df)), 8)):   # 切成 8 个文件
    pq.write_table(pa.Table.from_pandas(df.iloc[idx], preserve_index=False), f"dirty/part-{i}.parquet")
print("脏数据总行数:", len(df))
