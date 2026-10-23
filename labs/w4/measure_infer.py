"""在 CPU 上加载 Qwen2.5-0.5B，对比：估算的权重字节 vs 张量实际字节 vs 进程内存增量。"""
import argparse
import gc
import resource
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B")
ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float32"])
ap.add_argument("--gen", type=int, default=256, help="生成多少个 token 来观察 KV Cache")
a = ap.parse_args()
MiB = 2**20


def rss_mib() -> float:
    with open("/proc/self/status") as f:          # Linux；Mac 上见下方说明
        for line in f:
            if line.startswith("VmRSS"):
                return int(line.split()[1]) / 1024
    return float("nan")


base = rss_mib()
dtype = getattr(torch, a.dtype)
model = AutoModelForCausalLM.from_pretrained(a.model, dtype=dtype).eval()
gc.collect()
loaded = rss_mib()
n = sum(p.numel() for p in model.parameters())
tensor_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
print(f"{a.model} dtype={a.dtype} 参数量={n / 1e9:.3f}B")
print(f"估算权重 = 参数量 × {torch.tensor([], dtype=dtype).element_size()} 字节 = {tensor_bytes / MiB:.0f} MiB（张量实际字节）")
print(f"进程 RSS：加载前 {base:.0f} MiB → 加载后 {loaded:.0f} MiB，增量 {loaded - base:.0f} MiB")

tok = AutoTokenizer.from_pretrained(a.model)
ids = tok("Data platform engineers moving into AI infrastructure should", return_tensors="pt").input_ids
with torch.no_grad():
    out = model.generate(ids, max_new_tokens=a.gen, min_new_tokens=a.gen, do_sample=False,
                         return_dict_in_generate=True, pad_token_id=tok.eos_token_id)
cache = out.past_key_values
kv = sum(l.keys.numel() * l.keys.element_size() + l.values.numel() * l.values.element_size() for l in cache.layers)
T = out.sequences.shape[1]
c = model.config
formula = 2 * c.num_hidden_layers * c.num_key_value_heads * (c.hidden_size // c.num_attention_heads) * T * torch.tensor([], dtype=dtype).element_size()
print(f"生成后序列长度 T={T}：KV Cache 实测 {kv / MiB:.2f} MiB，公式 {formula / MiB:.2f} MiB")
print(f"生成结束后进程 RSS {rss_mib():.0f} MiB（权重页已被真正读入内存）")
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (2**20 if sys.platform == "darwin" else 1024)
print(f"进程峰值 RSS {peak:.0f} MiB")
