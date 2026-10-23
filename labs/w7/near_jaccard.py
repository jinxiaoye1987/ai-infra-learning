"""注入的近似重复与原文之间的真实 Jaccard 分布：解释为什么阈值 0.7 时只抓到一部分。"""
import glob, re
import numpy as np, pandas as pd

def shingles(text, n=5):
    w = re.findall(r"\w+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(max(1, len(w) - n + 1))}

df = pd.concat([pd.read_parquet(f) for f in glob.glob("input/*.parquet")]).set_index("id")
near = [i for i in df.index if i.endswith("-near")]
js = np.array([len((a := shingles(df.at[i[:-5], "text"])) & (b := shingles(df.at[i, "text"]))) / len(a | b) for i in near])
print(f"近似重复对 {len(js)} 个，Jaccard 中位数 {np.median(js):.3f}，均值 {js.mean():.3f}")
for lo, hi in [(0, .5), (.5, .6), (.6, .7), (.7, .8), (.8, 1.01)]:
    print(f"  [{lo:.1f}, {min(hi,1):.1f}) {((js >= lo) & (js < hi)).sum():5d}")
