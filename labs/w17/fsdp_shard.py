"""FSDP2（fully_shard）在 CPU/gloo 上的分片演示：每个 rank 实际持有多少参数与优化器状态，训练一步后与 DDP 结果一致。
用法：torchrun --nproc_per_node=N fsdp_shard.py"""
import torch, torch.nn as nn, torch.distributed as dist
from torch.distributed.fsdp import fully_shard
from torch.nn.parallel import DistributedDataParallel as DDP
dist.init_process_group("gloo"); r, n = dist.get_rank(), dist.get_world_size()
def make():
    torch.manual_seed(0)
    return nn.Sequential(*[nn.Sequential(nn.Linear(1024, 4096), nn.ReLU(), nn.Linear(4096, 1024)) for _ in range(4)])
def local_numel(m): return sum((p.to_local() if hasattr(p, "to_local") else p).numel() for p in m.parameters())
def step(m):
    opt = torch.optim.Adam(m.parameters(), lr=1e-3); torch.manual_seed(100 + r)
    loss = m(torch.randn(8, 1024)).pow(2).mean(); loss.backward(); opt.step()
    st = sum((v.to_local() if hasattr(v, "to_local") else v).numel() for s in opt.state.values() for v in s.values() if torch.is_tensor(v) and v.dim() > 0)
    return st
ddp = DDP(make()); s_ddp = step(ddp)
fs = make()
for blk in fs: fully_shard(blk)                       # 每个子块一个分片单元（用时 AllGather，用完释放）
fully_shard(fs); s_fs = step(fs)
total = sum(p.numel() for p in make().parameters())
full = {k: v.full_tensor() if hasattr(v, "full_tensor") else v for k, v in fs.state_dict().items()}
diff = max((full[k] - v).abs().max().item() for k, v in ddp.module.state_dict().items())
print(f"rank {r}/{n}: 模型共 {total/1e6:.1f}M 参数 | DDP 本地参数 {local_numel(ddp)/1e6:.1f}M 优化器状态 {s_ddp/1e6:.1f}M | "
      f"FSDP 本地参数 {local_numel(fs)/1e6:.1f}M 优化器状态 {s_fs/1e6:.1f}M | 一步后与 DDP 参数最大差 {diff:.1e}", flush=True)
dist.destroy_process_group()
