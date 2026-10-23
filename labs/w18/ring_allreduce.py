"""手写 Ring AllReduce（ReduceScatter + AllGather，各 n-1 步，只用相邻 rank 的 send/recv），与 dist.all_reduce 对比。
用法：torchrun --nproc_per_node=4 ring_allreduce.py"""
import torch, torch.distributed as dist
dist.init_process_group("gloo"); r, n = dist.get_rank(), dist.get_world_size()
torch.manual_seed(r); data = torch.randn(n * 1000)
ref = data.clone(); dist.all_reduce(ref)
chunks = list(data.clone().chunk(n)); right, left = (r + 1) % n, (r - 1) % n
sent = 0
for step in range(n - 1):                                # 阶段 1：ReduceScatter
    s, rcv = (r - step) % n, (r - step - 1) % n
    buf = torch.empty_like(chunks[rcv])
    req = dist.isend(chunks[s], right); dist.recv(buf, left); req.wait()
    chunks[rcv] += buf; sent += chunks[s].numel()
# 此时 chunks[(r+1)%n] 是全体之和的第 (r+1)%n 块
for step in range(n - 1):                                # 阶段 2：AllGather
    s, rcv = (r + 1 - step) % n, (r - step) % n
    buf = torch.empty_like(chunks[rcv])
    req = dist.isend(chunks[s], right); dist.recv(buf, left); req.wait()
    chunks[rcv] = buf; sent += chunks[s].numel()
out = torch.cat(chunks)
print(f"rank {r}: 与 dist.all_reduce 最大误差 {(out-ref).abs().max():.1e}，本 rank 发送 {sent} 个元素 = "
      f"{sent/data.numel():.2f}× 数据量（理论 2(n-1)/n = {2*(n-1)/n:.2f}）\n", end="", flush=True)
dist.destroy_process_group()
