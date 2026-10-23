"""权重量化的直观体验（CPU）：PyTorch 动态 INT8 量化 Linear 层，比较权重大小、decode 速度与输出。
注意：这与 GPU 上 AWQ/GPTQ/FP8 的实现完全不同，只用于体会“更小的权重 ↔ 精度/速度”的取舍。"""
import time, torch, io
from transformers import AutoTokenizer, AutoModelForCausalLM
torch.set_num_threads(8); name = "Qwen/Qwen2.5-0.5B-Instruct"
tok = AutoTokenizer.from_pretrained(name)
msgs = [{"role": "user", "content": "列出 HDFS 的三个核心组件。"}]
ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt", return_dict=True)
def size_mb(model):
    b = io.BytesIO(); torch.save(model.state_dict(), b); return b.tell() / 1e6
def run(model, label):
    with torch.no_grad():
        model.generate(**ids, max_new_tokens=8)                 # 预热
        t = time.perf_counter(); out = model.generate(**ids, max_new_tokens=64, do_sample=False)
        dt = time.perf_counter() - t
    n = out.shape[1] - ids["input_ids"].shape[1]
    text = tok.decode(out[0, ids["input_ids"].shape[1]:], skip_special_tokens=True).replace("\n", " ")
    print(f"[{label}] 权重 {size_mb(model):6.0f} MB  {n/dt:5.1f} tok/s\n  输出：{text[:90]}")
m = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32).eval()
run(m, "FP32")
q = torch.ao.quantization.quantize_dynamic(m, {torch.nn.Linear}, dtype=torch.qint8)
run(q, "INT8 动态量化")
