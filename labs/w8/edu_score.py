"""Ray Data 批量推理（CPU 版）：用 FineWeb-Edu 分类器给第 6 周的清洗结果打“教育价值”分。"""
import argparse
import os
import time

import numpy as np
import pandas as pd
import ray

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=2000)          # 打分的文档数
ap.add_argument("--actors", type=int, default=2)        # Actor 池大小（相当于 GPU 版的模型副本数）
ap.add_argument("--threads", type=int, default=2)       # 每个 Actor 的 torch 线程数
ap.add_argument("--batch", type=int, default=16)
ap.add_argument("--maxlen", type=int, default=512)
ap.add_argument("--blocks", type=int, default=0)        # >0 时先 repartition 成这么多个 block
a = ap.parse_args()
ray.init(num_cpus=8, include_dashboard=False, log_to_driver=False)
ray.data.DataContext.get_current().enable_progress_bars = False
MODEL = "HuggingFaceFW/fineweb-edu-classifier"

class EduScorer:
    def __init__(self):                                   # 每个 Actor 只加载一次模型
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        torch.set_num_threads(a.threads)
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(MODEL)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL).eval()

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        enc = self.tok(list(df["text"]), return_tensors="pt", padding="longest",
                       truncation=True, max_length=a.maxlen)
        with self.torch.inference_mode():
            s = self.model(**enc).logits.squeeze(-1).float().numpy()
        return pd.DataFrame({"id": df["id"], "score": s,
                             "int_score": np.clip(np.round(s), 0, 5).astype(int),
                             "n_tok": enc["attention_mask"].sum(1).numpy(),
                             "pid": os.getpid()})       # 记录是哪个 Actor 处理的

ds = ray.data.read_parquet("../w6/clean").select_columns(["id", "text"]).limit(a.n)
if a.blocks:
    ds = ds.repartition(a.blocks)
t0 = time.time()
out = ds.map_batches(EduScorer, batch_format="pandas", batch_size=a.batch,
                     compute=ray.data.ActorPoolStrategy(size=a.actors),
                     num_cpus=a.threads).to_pandas()
dt = time.time() - t0
print(f"actors={a.actors} threads={a.threads} batch={a.batch} blocks={a.blocks or '默认'}: {len(out)} 篇，{dt:.1f}s，"
      f"{len(out) / dt:.1f} 篇/s，{out['n_tok'].sum() / dt:.0f} token/s（含模型加载）")
print(f"实际参与计算的 Actor 数: {out['pid'].nunique()}")
print("int_score 分布:", out["int_score"].value_counts().sort_index().to_dict())
print(f"int_score>=3（FineWeb-Edu 的保留阈值）占比 {(out['int_score'] >= 3).mean():.1%}；平均输入 token {out['n_tok'].mean():.0f}")
