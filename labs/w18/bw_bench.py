"""仿 nccl-tests 的 all_reduce 带宽测试（gloo/CPU）：algbw = 数据量/时间，busbw = algbw × 2(n-1)/n。
用法：torchrun --nproc_per_node=4 bw_bench.py"""
import time, torch, torch.distributed as dist
dist.init_process_group("gloo"); r, n = dist.get_rank(), dist.get_world_size()
if r == 0: print(f"{'size':>10} {'time(ms)':>10} {'algbw(GB/s)':>12} {'busbw(GB/s)':>12}", flush=True)
for size in [2**k for k in range(10, 29, 3)]:              # 1KB … 256MB
    x = torch.ones(size // 4)                               # float32
    for _ in range(2): dist.all_reduce(x)                   # 预热
    iters = 20 if size < 2**24 else 5
    dist.barrier(); t = time.perf_counter()
    for _ in range(iters): dist.all_reduce(x)
    dt = (time.perf_counter() - t) / iters
    if r == 0:
        alg = size / dt / 1e9
        print(f"{size:>10} {dt*1000:>10.3f} {alg:>12.3f} {alg*2*(n-1)/n:>12.3f}", flush=True)
dist.destroy_process_group()
