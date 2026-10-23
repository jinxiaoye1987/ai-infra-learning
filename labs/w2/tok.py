"""对比三种分词器：GPT-2（2019）、o200k_base（GPT-4o 系列）、Qwen2.5（中文友好）。"""
import tiktoken
from transformers import AutoTokenizer

TEXTS = {
    "英文": "The quick brown fox jumps over the lazy dog.",
    "中文": "大数据架构师转型 AI Infra，需要理解 KV Cache。",
    "SQL": "SELECT city, count(DISTINCT user_id) FROM events GROUP BY city;",
    "数字": "2026-10-20 12345678.90",
}

gpt2 = tiktoken.get_encoding("gpt2")
o200k = tiktoken.get_encoding("o200k_base")
qwen = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B")  # 只下载分词器文件（几 MB）

print(f"词表大小: gpt2={gpt2.n_vocab} o200k={o200k.n_vocab} qwen2.5={len(qwen)}")
print(f"{'类型':<4} {'字符':>4} {'UTF8字节':>8} {'gpt2':>5} {'o200k':>6} {'qwen':>5}")
for name, s in TEXTS.items():
    n_g, n_o, n_q = len(gpt2.encode(s)), len(o200k.encode(s)), len(qwen.encode(s))
    print(f"{name:<4} {len(s):>5} {len(s.encode()):>9} {n_g:>5} {n_o:>6} {n_q:>5}")

s = TEXTS["中文"]
print("\nGPT-2 前 8 个 token 的字节:", [gpt2.decode_single_token_bytes(t) for t in gpt2.encode(s)[:8]])
print("Qwen 的切分:", [qwen.decode([i]) for i in qwen.encode(s)])
print("Qwen 切数字:", [qwen.decode([i]) for i in qwen.encode(TEXTS["数字"])][:12])
