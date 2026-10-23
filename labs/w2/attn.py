"""用 NumPy 手写因果自注意力（单头），再与 PyTorch 官方实现对数。"""
import numpy as np
import torch
import torch.nn.functional as F

rng = np.random.default_rng(0)
T, d_model, d_head = 4, 8, 4            # 4 个 token，隐藏维 8，单头维度 4
x = rng.standard_normal((T, d_model)).astype(np.float32)   # 已经过 embedding 的输入
Wq, Wk, Wv = (rng.standard_normal((d_model, d_head)).astype(np.float32) * 0.5 for _ in range(3))

Q, K, V = x @ Wq, x @ Wk, x @ Wv        # 每个 (T, d_head)
scores = Q @ K.T / np.sqrt(d_head)      # (T, T)：第 i 行 = token i 对所有 token 的“相关度”
mask = np.triu(np.ones((T, T), dtype=bool), k=1)   # 上三角 = 未来位置
scores[mask] = -np.inf                  # 因果掩码：不许看未来
w = np.exp(scores - scores.max(axis=1, keepdims=True))
w = w / w.sum(axis=1, keepdims=True)    # softmax，每行和为 1
out = w @ V                             # (T, d_head)：按权重对 V 加权求和

np.set_printoptions(precision=3, suppress=True)
print("注意力权重（行=查询 token，列=被看的 token）:\n", w)
ref = F.scaled_dot_product_attention(torch.from_numpy(Q)[None], torch.from_numpy(K)[None],
                                     torch.from_numpy(V)[None], is_causal=True)[0].numpy()
print("与 PyTorch SDPA 最大误差:", float(np.abs(out - ref).max()))

# KV Cache 的本质：第 T 个 token 的输出只依赖 q_T 和 全部 K、V
q_last = Q[-1:]                          # 只算最后一个 token 的 Q
s_last = q_last @ K.T / np.sqrt(d_head)
w_last = np.exp(s_last - s_last.max()); w_last /= w_last.sum()
print("只用最后一行 Q + 缓存的 K/V 重算最后一个输出，误差:", float(np.abs(w_last @ V - out[-1]).max()))
