"""同一模型，一次 generate 处理 1/4/8 条 prompt（静态 batch），看吞吐如何随 batch 变化。
说明：decode 每步都要读一遍全部权重，batch 越大，这次读取被越多请求分摊。"""
import time, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
torch.set_num_threads(8); name = "Qwen/Qwen2.5-0.5B-Instruct"
tok = AutoTokenizer.from_pretrained(name, padding_side="left")
m = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32).eval()
new = 64
for b in (1, 4, 8, 16):
    prompts = [f"写一段关于分布式系统的说明，编号{i}" for i in range(b)]
    x = tok(prompts, return_tensors="pt", padding=True)
    with torch.no_grad():
        t = time.perf_counter()
        m.generate(**x, max_new_tokens=new, min_new_tokens=new, do_sample=False)
        dt = time.perf_counter() - t
    print(f"batch={b:<3} 耗时 {dt:5.2f}s 总吞吐 {b*new/dt:6.1f} tok/s 单请求速度 {new/dt:5.1f} tok/s")
