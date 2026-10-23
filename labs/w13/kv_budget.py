"""由 config.json 估算：权重显存、每 token 的 KV Cache、给定显卡上的 KV 容量与并发上限。
用法：python kv_budget.py qwen2.5-7b-config.json --gpu-gb 24 --util 0.9 --ctx 4096"""
import json, argparse
p = argparse.ArgumentParser()
p.add_argument("config"); p.add_argument("--gpu-gb", type=float, default=24)
p.add_argument("--util", type=float, default=0.9)      # 对应 vLLM --gpu-memory-utilization
p.add_argument("--act-gb", type=float, default=1.5)    # 激活/CUDA graph/碎片的经验预留（假设值）
p.add_argument("--ctx", type=int, default=4096); p.add_argument("--block", type=int, default=16)
p.add_argument("--wbytes", type=float, default=2); p.add_argument("--kvbytes", type=float, default=2)
a = p.parse_args(); c = json.load(open(a.config))
H, L, I, V = c["hidden_size"], c["num_hidden_layers"], c["intermediate_size"], c["vocab_size"]
nh, kvh = c["num_attention_heads"], c["num_key_value_heads"]; hd = H // nh
# 参数量：attention(q,o: H*H；k,v: H*kvh*hd，含 qkv bias) + MLP(3*H*I) + 2 个 RMSNorm；embedding 与 lm_head 不共享
attn = 2 * H * H + 2 * H * kvh * hd + (H + 2 * kvh * hd)
mlp = 3 * H * I
params = L * (attn + mlp + 2 * H) + V * H * (1 if c.get("tie_word_embeddings") else 2) + H
w_gb = params * a.wbytes / 1e9
kv_tok = 2 * L * kvh * hd * a.kvbytes                     # K 和 V，每层每个 KV 头 hd 维
budget = a.gpu_gb * a.util - w_gb - a.act_gb
toks = int(budget * 1e9 // kv_tok); blocks = toks // a.block
print(f"参数量 ≈ {params/1e9:.2f} B，权重 {w_gb:.2f} GB（{a.wbytes:g} 字节/参数）")
print(f"注意力：{nh} 个 Q 头、{kvh} 个 KV 头（GQA {nh//kvh}:1），head_dim={hd}")
print(f"每 token KV Cache = 2×{L}×{kvh}×{hd}×{a.kvbytes:g} = {kv_tok/1024:.0f} KiB")
print(f"若不用 GQA（KV 头 = {nh}）：{2*L*nh*hd*a.kvbytes/1024:.0f} KiB/token")
print(f"KV 预算 = {a.gpu_gb}×{a.util} - {w_gb:.2f} - {a.act_gb} = {budget:.2f} GB")
print(f"可容纳 {toks:,} 个 token = {blocks:,} 个 block（block={a.block}）")
print(f"上下文 {a.ctx} 满长度时最多并发 {toks // a.ctx} 个请求")
