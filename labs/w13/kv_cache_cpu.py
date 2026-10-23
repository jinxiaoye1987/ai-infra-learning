"""在 CPU 上用真实小模型对比 有/无 KV Cache 的生成速度（transformers）。
无 cache 时每生成一个 token 都要把整个前缀重新算一遍：总计算量 O(n²)。"""
import time, torch, argparse
from transformers import AutoTokenizer, AutoModelForCausalLM
p = argparse.ArgumentParser(); p.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
p.add_argument("--new", type=int, default=128); a = p.parse_args()
torch.set_num_threads(8)
tok = AutoTokenizer.from_pretrained(a.model); m = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float32).eval()
ids = tok("请用三句话介绍分布式文件系统 HDFS 的设计。" * 8, return_tensors="pt").input_ids
print(f"模型 {a.model}，prompt {ids.shape[1]} token，生成 {a.new} token（贪心，固定长度）")
for use_cache in (True, False):
    with torch.no_grad():
        t = time.perf_counter()
        m.generate(ids, max_new_tokens=a.new, min_new_tokens=a.new, do_sample=False, use_cache=use_cache)
        dt = time.perf_counter() - t
    print(f"use_cache={use_cache!s:<5} 耗时 {dt:6.2f}s  {a.new/dt:6.1f} token/s")
