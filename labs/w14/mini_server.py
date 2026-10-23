"""最小 OpenAI 兼容推理服务（CPU，transformers）：/v1/models、/v1/chat/completions（支持 stream）、/metrics。
刻意不做 batching：一个全局锁让请求逐个执行——用来对照 vLLM 的 continuous batching。
用法：python mini_server.py --model Qwen/Qwen2.5-0.5B-Instruct --port 8000"""
import argparse, asyncio, json, threading, time, uuid
import torch, uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, Response
from prometheus_client import Histogram, Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer

p = argparse.ArgumentParser(); p.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
p.add_argument("--port", type=int, default=8000); p.add_argument("--threads", type=int, default=8)
a = p.parse_args(); torch.set_num_threads(a.threads)
tok = AutoTokenizer.from_pretrained(a.model)
model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float32).eval()
app = FastAPI(); lock = asyncio.Lock()
# 指标命名仿照 vLLM 的 vllm:* 指标（名称不同，含义相近）
TTFT = Histogram("mini_time_to_first_token_seconds", "TTFT", buckets=[.1, .25, .5, 1, 2, 4, 8, 16, 32, 64])
TPOT = Histogram("mini_time_per_output_token_seconds", "TPOT", buckets=[.01, .02, .04, .06, .08, .1, .15, .2, .5])
RUN = Gauge("mini_num_requests_running", "正在生成的请求数"); WAIT = Gauge("mini_num_requests_waiting", "排队中的请求数")
GEN = Counter("mini_generation_tokens_total", "已生成 token 总数")

def chunk(rid, text=None, finish=None):
    d = {"id": rid, "object": "chat.completion.chunk", "model": a.model,
         "choices": [{"index": 0, "delta": {"content": text} if text else {}, "finish_reason": finish}]}
    return f"data: {json.dumps(d, ensure_ascii=False)}\n\n"

@app.get("/v1/models")
def models(): return {"object": "list", "data": [{"id": a.model, "object": "model"}]}

@app.get("/metrics")
def metrics(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/v1/chat/completions")
async def chat(req: Request):
    body = await req.json(); t0 = time.perf_counter(); rid = "chatcmpl-" + uuid.uuid4().hex[:8]
    ids = tok.apply_chat_template(body["messages"], add_generation_prompt=True, return_tensors="pt", return_dict=True)
    max_new = body.get("max_tokens", 128)
    async def gen():
        WAIT.inc()
        async with lock:                               # 无 batching：逐个请求独占模型
            WAIT.dec(); RUN.inc()
            streamer = TextIteratorStreamer(tok, skip_prompt=True, skip_special_tokens=True)
            th = threading.Thread(target=model.generate, kwargs=dict(**ids, max_new_tokens=max_new,
                                  do_sample=False, streamer=streamer)); th.start()
            first = None; n = 0; it = iter(streamer)
            while True:
                piece = await asyncio.to_thread(next, it, None)
                if piece is None: break
                if not piece: continue
                n += 1; GEN.inc()
                if first is None: first = time.perf_counter(); TTFT.observe(first - t0)
                yield chunk(rid, piece)
            th.join(); RUN.dec()
            if first and n > 1: TPOT.observe((time.perf_counter() - first) / (n - 1))
        yield chunk(rid, finish="stop"); yield "data: [DONE]\n\n"
    if body.get("stream"):
        return StreamingResponse(gen(), media_type="text/event-stream")
    text = "".join([json.loads(c[6:])["choices"][0]["delta"].get("content", "") async for c in gen() if c.startswith("data: {")])
    return {"id": rid, "object": "chat.completion", "model": a.model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}]}

uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
