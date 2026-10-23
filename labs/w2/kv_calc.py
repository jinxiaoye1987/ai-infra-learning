"""从 config.json 估算：权重大小、每 token KV、给定显存能放多少并发。"""
import argparse
import json
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
ap.add_argument("--params-b", type=float, required=True, help="参数量（十亿），以模型卡为准")
ap.add_argument("--gpu-gb", type=float, default=24)
ap.add_argument("--ctx", type=int, default=32768)
ap.add_argument("--reserve-gb", type=float, default=2, help="运行时/激活预留（经验值）")
a = ap.parse_args()

url = f"https://huggingface.co/{a.model}/raw/main/config.json"
c = json.load(urllib.request.urlopen(url))
L, H, Hkv, C = c["num_hidden_layers"], c["num_attention_heads"], c.get("num_key_value_heads", c["num_attention_heads"]), c["hidden_size"]
d = c.get("head_dim") or C // H
kv_tok = 2 * L * Hkv * d * 2                       # BF16 = 2 字节
w_gb = a.params_b * 1e9 * 2 / 2**30
free_gb = a.gpu_gb - w_gb - a.reserve_gb
print(f"{a.model}: L={L} H={H} H_kv={Hkv} d_head={d}")
print(f"权重(BF16) ≈ {w_gb:.1f} GiB；每 token KV = {kv_tok} B = {kv_tok/1024:.0f} KiB")
print(f"单条 {a.ctx} token 请求 KV = {kv_tok*a.ctx/2**30:.2f} GiB")
print(f"{a.gpu_gb:.0f} GB 卡剩余给 KV ≈ {free_gb:.1f} GiB → 约 {int(free_gb*2**30/kv_tok):,} 个 token，"
      f"≈ {free_gb*2**30/(kv_tok*a.ctx):.1f} 条满上下文请求")
if Hkv != H:
    print(f"若没有 GQA（H_kv={H}），每 token KV 将是 {2*L*H*d*2//1024} KiB，是现在的 {H//Hkv} 倍")
