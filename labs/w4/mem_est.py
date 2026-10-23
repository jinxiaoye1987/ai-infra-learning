"""显存估算器：读 HF config.json，估算参数量、推理显存、训练显存。
适用于 Llama / Qwen2 / Mistral 这类“GQA 注意力 + SwiGLU MLP”的 decoder-only 模型。
所有结果都是估算（不含 CUDA 上下文、分配器碎片、通信缓冲区等）。
"""
import argparse
import json
import pathlib
import urllib.request

BYTES = {"fp32": 4, "bf16": 2, "fp16": 2, "int8": 1, "int4": 0.5}
GiB = 2**30


def load_config(model: str) -> dict:
    p = pathlib.Path(model)
    if p.exists():
        return json.loads(p.read_text())
    return json.load(urllib.request.urlopen(f"https://huggingface.co/{model}/raw/main/config.json"))


def count_params(c: dict) -> dict:
    h, L, V, I = c["hidden_size"], c["num_hidden_layers"], c["vocab_size"], c["intermediate_size"]
    H = c["num_attention_heads"]
    Hkv = c.get("num_key_value_heads", H)
    d = c.get("head_dim") or h // H
    qkv_bias = c.get("model_type") == "qwen2"            # Qwen2 的 q/k/v 投影带偏置
    attn = h * H * d + 2 * h * Hkv * d + H * d * h        # Wq + Wk + Wv + Wo
    if qkv_bias:
        attn += H * d + 2 * Hkv * d
    mlp = 3 * h * I                                        # SwiGLU：gate、up、down 三个矩阵
    norms = 2 * h                                          # 每层两个 RMSNorm
    embed = V * h
    head = 0 if c.get("tie_word_embeddings", False) else V * h
    total = embed + L * (attn + mlp + norms) + h + head
    return {"embed": embed, "per_layer": attn + mlp + norms, "attn": attn, "mlp": mlp,
            "head": head, "total": total, "L": L, "Hkv": Hkv, "d": d, "h": h, "H": H}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct", help="HF 模型名或本地 config.json 路径")
    ap.add_argument("--dtype", default="bf16", choices=BYTES)
    ap.add_argument("--kv-dtype", default="bf16", choices=BYTES)
    ap.add_argument("--seq", type=int, default=4096)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--gpus", type=int, default=1, help="训练时的数据并行卡数（用于 ZeRO 切分）")
    ap.add_argument("--micro-batch", type=int, default=1)
    ap.add_argument("--train-seq", type=int, default=2048)
    a = ap.parse_args()

    c = load_config(a.model)
    p = count_params(c)
    N = p["total"]
    print(f"== {a.model}")
    print(f"参数量估算: {N / 1e9:.3f}B（嵌入 {p['embed'] / 1e6:.0f}M，每层 {p['per_layer'] / 1e6:.1f}M × {p['L']} 层，"
          f"lm_head {'共享' if p['head'] == 0 else f'{p['head'] / 1e6:.0f}M'}）")

    # ---- 推理 ----
    w = N * BYTES[a.dtype]
    kv_tok = 2 * p["L"] * p["Hkv"] * p["d"] * BYTES[a.kv_dtype]
    kv = kv_tok * a.seq * a.batch
    print(f"[推理] 权重 {a.dtype}: {w / GiB:.1f} GiB；KV 每 token {kv_tok / 1024:.0f} KiB；"
          f"batch={a.batch} × seq={a.seq} 的 KV: {kv / GiB:.1f} GiB；合计 ≈ {(w + kv) / GiB:.1f} GiB")

    # ---- 训练（混合精度 + AdamW）----
    # 口径来自 ZeRO 论文：bf16 参数 2 + bf16 梯度 2 + fp32 主参数 4 + Adam m 4 + Adam v 4 = 16 字节/参数
    n = a.gpus
    zero = {
        "无 ZeRO（DDP）": 2 * N + 2 * N + 12 * N,
        "ZeRO-1（切优化器状态）": 2 * N + 2 * N + 12 * N / n,
        "ZeRO-2（再切梯度）": 2 * N + (2 * N + 12 * N) / n,
        "ZeRO-3 / FSDP（全切）": 16 * N / n,
    }
    # 激活：Korthikanti et al. 2022（arXiv:2205.05198）每层 s·b·h·(34 + 5·a·s/h) 字节，
    # 假设 16 位激活、无张量并行、无重计算、含 dropout mask；用 FlashAttention 时 5as/h 项基本消失。
    s, b, h, H = a.train_seq, a.micro_batch, p["h"], p["H"]
    act_naive = p["L"] * s * b * h * (34 + 5 * H * s / h)
    act_flash = p["L"] * s * b * h * 34
    print(f"[训练] 混合精度 AdamW，固定部分 16 字节/参数，数据并行 {n} 卡时每卡：")
    for k, v in zero.items():
        print(f"    {k:<22} {v / GiB:8.1f} GiB")
    print(f"    + 激活（micro_batch={b}, seq={s}）：朴素注意力 ≈ {act_naive / GiB:.1f} GiB，"
          f"FlashAttention ≈ {act_flash / GiB:.1f} GiB（全量重计算可降到每层只存输入 ≈ {p['L'] * s * b * h * 2 / GiB:.2f} GiB）")
    lora = 2 * N  # 冻结的 bf16 底座；LoRA 适配器本身通常 < 1% 参数，这里忽略
    print(f"[LoRA] 底座 bf16 冻结 ≈ {lora / GiB:.1f} GiB + 适配器与其优化器状态（通常 < 1 GiB）+ 激活")


if __name__ == "__main__":
    main()
