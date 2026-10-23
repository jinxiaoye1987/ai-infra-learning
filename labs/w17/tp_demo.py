"""张量并行的最小演示（2 进程，gloo/CPU）：MLP 的第一层按列切、第二层按行切（Megatron 方式），
每层只需一次 AllReduce，结果与单机完全一致。用法：torchrun --nproc_per_node=2 tp_demo.py"""
import torch, torch.distributed as dist
dist.init_process_group("gloo"); r, n = dist.get_rank(), dist.get_world_size()
torch.manual_seed(0)                                   # 所有进程生成相同的完整权重，便于对照
x = torch.randn(4, 8); A = torch.randn(8, 16); B = torch.randn(16, 8)
ref = torch.relu(x @ A) @ B                            # 单机结果
A_i = A.chunk(n, dim=1)[r]                             # 列切：每个 rank 得到 8×(16/n)
B_i = B.chunk(n, dim=0)[r]                             # 行切：每个 rank 得到 (16/n)×8
y = torch.relu(x @ A_i) @ B_i                          # 本地计算，激活无需通信（GeLU/ReLU 逐元素）
dist.all_reduce(y)                                     # 部分和相加：整个 MLP 只此一次通信
print(f"rank {r}: A 分片 {tuple(A_i.shape)} B 分片 {tuple(B_i.shape)}，与单机结果最大误差 {(y-ref).abs().max():.2e}", flush=True)
dist.destroy_process_group()
