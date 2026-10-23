"""用真实的 GPT-2（124M）观察 KV Cache：形状、字节数、开/关缓存的速度差。"""
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

torch.manual_seed(0)
torch.set_num_threads(4)
tok = AutoTokenizer.from_pretrained("openai-community/gpt2")
model = AutoModelForCausalLM.from_pretrained("openai-community/gpt2").eval()
cfg = model.config
print(f"层数={cfg.n_layer} 头数={cfg.n_head} 隐藏维={cfg.n_embd} 每头维度={cfg.n_embd // cfg.n_head}")
print(f"参数量={sum(p.numel() for p in model.parameters()) / 1e6:.1f}M")

ids = tok("The data warehouse architect opened the notebook and", return_tensors="pt").input_ids
print("prompt token 数:", ids.shape[1])

# ① 一次前向（prefill），拿到缓存
with torch.no_grad():
    out = model(ids, use_cache=True)
kv = out.past_key_values
k0 = kv.layers[0].keys if hasattr(kv, "layers") else kv[0][0]
print("第 0 层 K 的形状 (batch, 头数, 序列长度, 每头维度):", tuple(k0.shape), k0.dtype)


def cache_bytes(cache) -> int:
    layers = cache.layers if hasattr(cache, "layers") else cache
    return sum(l.keys.numel() * l.keys.element_size() + l.values.numel() * l.values.element_size()
               if hasattr(l, "keys") else l[0].nbytes + l[1].nbytes for l in layers)


T = ids.shape[1]
formula = 2 * cfg.n_layer * cfg.n_head * (cfg.n_embd // cfg.n_head) * T * 1 * 4
print(f"实测缓存字节={cache_bytes(kv)}  公式 2×L×H×d×T×B×4字节={formula}")

# ② 生成 200 个新 token：开缓存 vs 关缓存（贪心解码，结果应完全相同）
for use_cache in (True, False):
    t = time.perf_counter()
    with torch.no_grad():
        g = model.generate(ids, max_new_tokens=200, min_new_tokens=200, do_sample=False,
                           use_cache=use_cache, pad_token_id=tok.eos_token_id)
    dt = time.perf_counter() - t
    print(f"use_cache={use_cache!s:<5} 生成 200 token 用时 {dt:6.2f}s  ≈{200 / dt:5.1f} token/s  末尾 id={g[0, -5:].tolist()}")
