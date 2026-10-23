"""前缀缓存的收益（CPU 真实模型）：多个请求共享同一段很长的 system prompt。
不复用：每个请求都 prefill 全部 token；复用：system prompt 的 KV 只算一次，之后每个请求只 prefill 自己的问题。
这里只测 prefill（即 TTFT 的计算部分）。"""
import copy, time, torch
from transformers import AutoTokenizer, AutoModelForCausalLM, DynamicCache
torch.set_num_threads(8); name = "Qwen/Qwen2.5-0.5B-Instruct"
tok = AutoTokenizer.from_pretrained(name); m = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32).eval()
system = "你是公司内部的数据平台助手。以下是平台规范：" + "所有 Hive 表必须按日期分区，保留 90 天；Spark 作业必须设置队列和最大 executor 数；" * 40
questions = ["Hive 表要保留多久？", "Spark 作业要设置什么？", "分区字段是什么？", "谁负责审批？"]
sys_ids = tok(system, return_tensors="pt").input_ids
q_ids = [tok(q, return_tensors="pt").input_ids for q in questions]
print(f"system prompt {sys_ids.shape[1]} token，问题平均 {sum(q.shape[1] for q in q_ids)/len(q_ids):.0f} token，共 {len(questions)} 个请求")
with torch.no_grad():
    m(torch.cat([sys_ids, q_ids[0]], 1))                        # 预热
    t = time.perf_counter()
    for q in q_ids: m(torch.cat([sys_ids, q], 1))               # 不复用：整段 prefill
    full = (time.perf_counter() - t) / len(q_ids)
    t = time.perf_counter(); cache = DynamicCache(); m(sys_ids, past_key_values=cache, use_cache=True)
    once = time.perf_counter() - t                              # 前缀只算一次
    t = time.perf_counter()
    for q in q_ids:
        c = copy.deepcopy(cache)                                # 每个请求从共享前缀出发（引擎中是共享块，不需复制）
        m(q, past_key_values=c, use_cache=True)
    reuse = (time.perf_counter() - t) / len(q_ids)
print(f"不复用：每请求 prefill {full*1000:7.1f} ms")
print(f"复用：  前缀一次性 {once*1000:7.1f} ms，之后每请求 {reuse*1000:7.1f} ms（含复制 cache 的开销）")
print(f"命中前缀后 TTFT 计算部分降为 {reuse/full:.1%}")
