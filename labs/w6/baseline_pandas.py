"""对照：同样的 normalize + quality 逻辑，用单进程 pandas 跑一遍。"""
import glob
import time

import pandas as pd

from clean_funcs import normalize, quality

t = time.time()
df = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob("dirty/*.parquet"))], ignore_index=True)
df = quality(normalize(df))
print(df["reason"].replace("", "(通过)").value_counts().to_string())
print("单进程 pandas 用时 %.1fs" % (time.time() - t))
