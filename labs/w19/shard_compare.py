"""全参训练 SmolLM2-135M：DDP vs FSDP2，2 个 CPU 进程（gloo）。比较每 rank 持有的参数/梯度/优化器状态字节数、峰值内存与每步耗时。
用法：torchrun --nproc_per_node=2 shard_compare.py ddp|fsdp"""
import sys, time, resource, torch, torch.distributed as dist
import pyarrow.parquet as pq
from transformers import AutoTokenizer, AutoModelForCausalLM
from torch.distributed.fsdp import fully_shard
from torch.nn.parallel import DistributedDataParallel as DDP
mode = sys.argv[1]; dist.init_process_group("gloo"); r, n = dist.get_rank(), dist.get_world_size()
torch.set_num_threads(4); torch.manual_seed(0)
name = "HuggingFaceTB/SmolLM2-135M"
tok = AutoTokenizer.from_pretrained(name); tok.pad_token = tok.pad_token or tok.eos_token  # SmolLM2 没有 pad token（本站实测报错）
model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32)
if mode == "ddp":
    model = DDP(model)
else:
    for layer in model.model.layers: fully_shard(layer)  # 每个 Transformer 层一个分片单元
    fully_shard(model)
opt = torch.optim.AdamW(model.parameters(), lr=1e-5)
texts = pq.read_table("../w7/input/part-0.parquet", columns=["text"]).column("text").to_pylist()
def local(t): return t.to_local() if hasattr(t, "to_local") else t
times = []
for step in range(6):
    batch = tok(texts[(step * n + r) * 2:(step * n + r) * 2 + 2], return_tensors="pt", truncation=True, max_length=128, padding="max_length")
    t = time.perf_counter()
    out = model(**batch, labels=batch.input_ids); out.loss.backward(); opt.step(); opt.zero_grad(set_to_none=False)
    times.append(time.perf_counter() - t)
mb = lambda xs: sum(local(x).numel() * local(x).element_size() for x in xs) / 1e6
p_mb = mb(list(model.parameters())); g_mb = mb([p.grad for p in model.parameters() if p.grad is not None])
o_mb = mb([v for s in opt.state.values() for v in s.values() if torch.is_tensor(v) and v.dim() > 0])
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
loss = out.loss.detach(); dist.all_reduce(loss); loss /= n
msg = (f"[{mode}] rank {r}: 参数 {p_mb:6.0f}MB 梯度 {g_mb:6.0f}MB 优化器 {o_mb:6.0f}MB 合计 {p_mb+g_mb+o_mb:6.0f}MB | "
       f"进程峰值内存 {peak:6.0f}MB | 每步 {sum(times[1:])/len(times[1:]):.2f}s | 第 6 步 loss {loss.item():.3f}")
for i in range(n):
    if i == r: print(msg, flush=True)
    dist.barrier()
dist.destroy_process_group()
