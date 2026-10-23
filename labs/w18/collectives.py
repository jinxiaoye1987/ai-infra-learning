"""五个集合通信原语一次看全（gloo/CPU）。用法：torchrun --nproc_per_node=4 collectives.py"""
import torch, torch.distributed as dist
dist.init_process_group("gloo"); r, n = dist.get_rank(), dist.get_world_size()
def show(name, val):                                   # 按 rank 顺序打印，避免输出交错
    for i in range(n):
        if i == r: print(f"rank {r} {name:<15} {val}", flush=True)
        dist.barrier()
x = torch.tensor([float(r + 1)]); dist.all_reduce(x); show("all_reduce", x.tolist())
out = [torch.zeros(1) for _ in range(n)]; dist.all_gather(out, torch.tensor([float(r)])); show("all_gather", [t.item() for t in out])
inp = [torch.tensor([float(10 * r + j)]) for j in range(n)]          # rank r 的第 j 块
rs = torch.zeros(1); dist.reduce_scatter(rs, inp); show("reduce_scatter", rs.tolist())
b = torch.tensor([float(r)]) if r == 0 else torch.zeros(1); b += 42 if r == 0 else 0
dist.broadcast(b, src=0); show("broadcast", b.tolist())
a2a_in = [torch.tensor([float(10 * r + j)]) for j in range(n)]       # 发给 rank j 的数据
a2a_out = [torch.zeros(1) for _ in range(n)]
try:
    dist.all_to_all(a2a_out, a2a_in); show("all_to_all", [t.item() for t in a2a_out])
except Exception as e:
    show("all_to_all", f"不支持：{type(e).__name__}: {str(e)[:60]}")
dist.destroy_process_group()
