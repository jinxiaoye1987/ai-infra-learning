"""把一次训练迭代拆开，逐项测量：参数、梯度、AdamW 状态、激活（反向需要保存的张量）。
在 nanoGPT 目录下运行：python mem_parts.py --batch_size 12 --block_size 64
"""
import argparse

import torch
from model import GPT, GPTConfig  # nanoGPT 自带的 model.py

ap = argparse.ArgumentParser()
ap.add_argument("--batch_size", type=int, default=12)
ap.add_argument("--block_size", type=int, default=64)
ap.add_argument("--n_layer", type=int, default=4)
ap.add_argument("--n_head", type=int, default=4)
ap.add_argument("--n_embd", type=int, default=128)
ap.add_argument("--no-flash", action="store_true", help="改用朴素注意力（显式构造 T×T 矩阵）")
a = ap.parse_args()
MiB = 2**20

torch.manual_seed(0)
cfg = GPTConfig(block_size=a.block_size, vocab_size=65, n_layer=a.n_layer, n_head=a.n_head,
                n_embd=a.n_embd, dropout=0.0, bias=False)
model = GPT(cfg)
if a.no_flash:
    for blk in model.transformer.h:
        blk.attn.flash = False  # nanoGPT 只在非 flash 模式下才注册掩码 buffer，这里手动补上
        blk.attn.register_buffer("bias", torch.tril(torch.ones(a.block_size, a.block_size))
                                 .view(1, 1, a.block_size, a.block_size))
opt = model.configure_optimizers(weight_decay=0.1, learning_rate=1e-3, betas=(0.9, 0.99), device_type="cpu")

def nbytes(ts):
    return sum(t.numel() * t.element_size() for t in ts)

x = torch.randint(0, 65, (a.batch_size, a.block_size))
y = torch.randint(0, 65, (a.batch_size, a.block_size))

# ① 前向：用 saved_tensors_hooks 统计 autograd 为反向“存下来”的张量 = 激活
param_ptrs = {p.data_ptr() for p in model.parameters()}
saved = {}  # 按底层存储地址去重：同一块内存被多处保存只算一次；权重本身不算激活
def pack(t):
    ptr = t.untyped_storage().data_ptr()
    if ptr not in param_ptrs:
        saved[ptr] = t.untyped_storage().nbytes()
    return t
with torch.autograd.graph.saved_tensors_hooks(pack, lambda t: t):
    logits, loss = model(x, y)
act = sum(saved.values())

# ② 反向：产生梯度；③ 优化器 step：第一次 step 时才分配 exp_avg / exp_avg_sq
loss.backward()
grads = nbytes(p.grad for p in model.parameters() if p.grad is not None)
opt.step()
states = nbytes(v for s in opt.state.values() for v in s.values() if torch.is_tensor(v))
params = nbytes(model.parameters())

print(f"配置 B={a.batch_size} T={a.block_size} L={a.n_layer} C={a.n_embd} {'朴素注意力' if a.no_flash else 'SDPA'}  参数量={sum(p.numel() for p in model.parameters()):,}")
print(f"参数      {params / MiB:8.2f} MiB  (fp32 = 4 字节/参数)")
print(f"梯度      {grads / MiB:8.2f} MiB  (与参数同形状)")
print(f"AdamW状态 {states / MiB:8.2f} MiB  (exp_avg + exp_avg_sq = 2 × 参数)")
print(f"激活      {act / MiB:8.2f} MiB  (随 B×T 增长；去重后 {len(saved)} 块存储)")
print(f"合计      {(params + grads + states + act) / MiB:8.2f} MiB")
