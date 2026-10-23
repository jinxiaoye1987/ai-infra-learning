"""毕业项目 A 的最小可运行版本：清洗结果 → 精确去重 → MinHash 近重复去重 → 教育价值打分 → 过滤 → 带版本输出 + manifest + MLflow。
CPU 单机版，用 pandas 串起来；每一步都对应第 6–8 周的 Ray/Spark 实现，规模变大时逐步替换。
用法：python pipeline.py --input ../w6/clean --n 600 --threshold 2"""
import argparse, datetime, hashlib, json, os, subprocess, time
import numpy as np, pandas as pd, pyarrow.dataset as pads
from datasketch import MinHash, MinHashLSH

p = argparse.ArgumentParser()
p.add_argument("--input", default="../w6/clean"); p.add_argument("--n", type=int, default=600)
p.add_argument("--threshold", type=int, default=2)           # 保留 int_score >= threshold（FineWeb-Edu 用 3）
p.add_argument("--jaccard", type=float, default=0.8); p.add_argument("--out", default="dataset")
a = p.parse_args()
stats, timing = {}, {}
def stage(name):
    def deco(f):
        def run(df):
            t = time.perf_counter(); out = f(df); timing[name] = round(time.perf_counter() - t, 2)
            n_in = 0 if df is None else len(df)
            stats[name] = {"in": n_in, "out": len(out)}; print(f"[{name:<10}] {n_in:>5} → {len(out):>5}  {timing[name]:6.2f}s", flush=True)
            return out
        return run
    return deco

@stage("load")
def load(_):
    return pads.dataset(a.input).to_table(columns=["id", "text"]).slice(0, a.n).to_pandas()

@stage("exact")
def exact(df):                                               # 第 7 周：规范化后哈希
    key = df.text.map(lambda s: hashlib.md5(" ".join(s.lower().split()).encode()).hexdigest())
    return df.loc[~key.duplicated()]

@stage("minhash")
def near(df):                                                # 第 7 周：MinHash + LSH（单机版）
    lsh = MinHashLSH(threshold=a.jaccard, num_perm=128); keep = []
    for i, t in zip(df.id, df.text):
        toks = t.lower().split(); sh = {" ".join(toks[j:j + 5]).encode() for j in range(max(1, len(toks) - 4))}
        m = MinHash(num_perm=128); m.update_batch(list(sh))
        if not lsh.query(m): lsh.insert(i, m); keep.append(i)
    return df[df.id.isin(keep)]

@stage("score")
def score(df):                                               # 第 8 周：FineWeb-Edu 分类器批量推理（CPU）
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    torch.set_num_threads(8); name = "HuggingFaceFW/fineweb-edu-classifier"
    tok = AutoTokenizer.from_pretrained(name); m = AutoModelForSequenceClassification.from_pretrained(name).eval()
    scores = []
    for s in range(0, len(df), 16):
        enc = tok(list(df.text[s:s + 16]), return_tensors="pt", padding="longest", truncation=True, max_length=512)
        with torch.inference_mode(): scores += m(**enc).logits.squeeze(-1).tolist()
    df = df.assign(score=np.round(scores, 3)); return df.assign(int_score=np.clip(np.round(df.score), 0, 5).astype(int))

@stage("filter")
def filt(df): return df[df.int_score >= a.threshold]

t0 = time.perf_counter()
df = filt(score(near(exact(load(None)))))
try: rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
except Exception: rev = "nogit"
params = {"input": a.input, "n": a.n, "threshold": a.threshold, "jaccard": a.jaccard, "code_rev": rev}
ver = f"v{datetime.date.today():%Y%m%d}-{rev}-" + hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:6]
out = os.path.join(a.out, ver); os.makedirs(out, exist_ok=True)
df.to_parquet(os.path.join(out, "part-0.parquet"), index=False)
manifest = {"version": ver, "created": datetime.datetime.now().isoformat(timespec="seconds"), "params": params,
            "stages": stats, "seconds": timing, "rows": len(df), "int_score_hist": df.int_score.value_counts().sort_index().to_dict()}
json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), ensure_ascii=False, indent=1, default=int)
try:                                                          # 第 20 周：把这次运行记录到 MLflow
    import mlflow; mlflow.set_experiment("data-pipeline")
    with mlflow.start_run(run_name=ver):
        mlflow.log_params(params); mlflow.log_metrics({f"rows_{k}": v["out"] for k, v in stats.items()})
        mlflow.log_artifact(os.path.join(out, "manifest.json"))
except Exception as e: print("MLflow 未记录：", e)
print(f"输出 {out}/  共 {len(df)} 行，总耗时 {time.perf_counter()-t0:.1f}s")
