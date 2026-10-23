"""GPT-2 small（124M，随机初始化，不需下载权重）一次训练迭代的内存账：实测 vs 估算。"""
import argparse

import torch
from transformers import GPT2Config, GPT2LMHeadModel

ap = argparse.ArgumentParser()
ap.add_argument("--batch", type=int, default=4)
ap.add_argument("--seq", type=int, default=256)
ap.add_argument("--dropout", type=float, default=0.1, help="GPT-2 默认 0.1；设 0 关闭全部 dropout")
a = ap.parse_args()
MiB = 2**20
torch.manual_seed(0)

cfg = GPT2Config(n_positions=1024, attn_implementation="sdpa",
                 resid_pdrop=a.dropout, embd_pdrop=a.dropout, attn_pdrop=a.dropout)   # 与官方 gpt2 相同的结构超参
model = GPT2LMHeadModel(cfg).train()
opt = torch.optim.AdamW(model.parameters(), lr=1e-4)
N = sum(p.numel() for p in model.parameters())

x = torch.randint(0, cfg.vocab_size, (a.batch, a.seq))
param_ptrs = {p.data_ptr() for p in model.parameters()}
saved = {}
def pack(t):
    ptr = t.untyped_storage().data_ptr()
    if ptr not in param_ptrs:
        saved[ptr] = t.untyped_storage().nbytes()
    return t
with torch.autograd.graph.saved_tensors_hooks(pack, lambda t: t):
    loss = model(input_ids=x, labels=x).loss
act = sum(saved.values())
loss.backward()
opt.step()

P = sum(p.numel() * p.element_size() for p in model.parameters())
G = sum(p.grad.numel() * p.grad.element_size() for p in model.parameters())
S = sum(v.numel() * v.element_size() for st in opt.state.values() for v in st.values() if torch.is_tensor(v) and v.dim() > 0)
L, h, H, s, b = cfg.n_layer, cfg.n_embd, cfg.n_head, a.seq, a.batch
logits = b * s * cfg.vocab_size * 4
print(f"GPT-2 small 参数量 N={N:,}  batch={b} seq={s} dropout={a.dropout}  fp32 训练")
print(f"{'项目':<10}{'实测 MiB':>10}{'估算 MiB':>10}  估算口径")
print(f"{'参数':<10}{P / MiB:>10.1f}{4 * N / MiB:>10.1f}  4N")
print(f"{'梯度':<10}{G / MiB:>10.1f}{4 * N / MiB:>10.1f}  4N")
print(f"{'AdamW':<10}{S / MiB:>10.1f}{8 * N / MiB:>10.1f}  8N")
print(f"{'激活':<10}{act / MiB:>10.1f}{(L * s * b * h * 34 * 2 + logits * 2) / MiB:>10.1f}  Korthikanti 34sbh×L（16 位口径×2 换成 fp32）+ logits 及其 softmax")
print(f"logits 一项 = b×s×V×4 字节 = {logits / MiB:.1f} MiB（词表 {cfg.vocab_size}，常被忽略的大头）")
