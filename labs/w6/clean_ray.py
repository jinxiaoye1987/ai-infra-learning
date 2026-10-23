"""实验 2：Ray Data 清洗管线：规范化 → 启发式质量过滤（Gopher 规则子集）→ 统计 token → 写出。"""
import argparse
import time

import pandas as pd
import ray
from ray.data.expressions import col

from clean_funcs import normalize, quality

ap = argparse.ArgumentParser()
ap.add_argument("--input", default="dirty/")
ap.add_argument("--output", default="clean/")
ap.add_argument("--cpus", type=int, default=4)
a = ap.parse_args()
ray.init(num_cpus=a.cpus, include_dashboard=False)


class TokenCounter:
    """有状态 UDF：每个 Actor 只加载一次分词器（模拟“加载一次模型”）。"""
    def __init__(self):
        import tiktoken
        self.enc = tiktoken.get_encoding("gpt2")

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        df["n_tokens"] = [len(x) for x in self.enc.encode_ordinary_batch(df["text"].tolist())]
        return df


t = time.time()
ds = (ray.data.read_parquet(a.input)
      .map_batches(normalize, batch_format="pandas")
      .map_batches(quality, batch_format="pandas"))
tagged = ds.materialize()                                   # 物化一次，下面两处复用
print("按原因统计:")
for r in sorted(tagged.groupby("reason").count().take_all(), key=lambda x: -x["count()"]):
    print(f"  {r['reason'] or '(通过)':<16}{r['count()']:>7}")

kept = (tagged.filter(expr=col("reason") == "")             # 表达式过滤：走 Arrow 原生实现
        .drop_columns(["reason"])
        .map_batches(TokenCounter, batch_format="pandas",
                     compute=ray.data.ActorPoolStrategy(size=2)))   # 固定 2 个 Actor
kept.write_parquet(a.output)
print("清洗用时 %.1fs" % (time.time() - t))
print("---- 执行统计（节选）----")
for line in kept.stats().splitlines():
    if line.startswith("Operator") or "Remote wall time" in line or "tasks executed" in line:
        print(line.strip()[:150])

out = ray.data.read_parquet(a.output)
print("保留行数:", out.count(), " 总 token 数(GPT-2 分词):", out.sum("n_tokens"))
