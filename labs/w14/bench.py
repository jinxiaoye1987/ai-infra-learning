# bench.py —— 并发流式请求，统计 TTFT / TPOT / 吞吐（对任何 OpenAI 兼容服务可用：vLLM、SGLang、mini_server）
import asyncio, time, argparse, statistics
from openai import AsyncOpenAI

async def one(cli, model, prompt, max_tokens):
    t0 = time.perf_counter(); first = None; n = 0
    stream = await cli.chat.completions.create(model=model, stream=True, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}])
    async for ch in stream:
        if ch.choices and ch.choices[0].delta.content:
            n += 1                        # 近似：按流式 chunk 计数（vLLM 通常 1 chunk ≈ 1 token）
            if first is None: first = time.perf_counter()
    t2 = time.perf_counter()
    return first - t0, (t2 - first) / max(n - 1, 1), n

async def main(a):
    cli = AsyncOpenAI(base_url=a.url, api_key="x", timeout=600)
    sem = asyncio.Semaphore(a.concurrency)
    async def run(i):
        async with sem:
            return await one(cli, a.model, f"写一段 300 字关于分布式系统的说明，编号{i}", a.max_tokens)
    t = time.perf_counter()
    res = await asyncio.gather(*[run(i) for i in range(a.n)])
    dur = time.perf_counter() - t
    ttft = [r[0] for r in res]; tpot = [r[1] for r in res]; toks = sum(r[2] for r in res)
    q = lambda xs, p: sorted(xs)[max(int(len(xs) * p) - 1, 0)]
    print(f"并发={a.concurrency} 请求={a.n} 耗时={dur:.1f}s 吞吐={toks/dur:.1f} tok/s")
    print(f"TTFT p50={statistics.median(ttft)*1000:.0f}ms p95={q(ttft,.95)*1000:.0f}ms")
    print(f"TPOT p50={statistics.median(tpot)*1000:.1f}ms p95={q(tpot,.95)*1000:.1f}ms")

p = argparse.ArgumentParser()
p.add_argument("--url", default="http://localhost:8000/v1")
p.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
p.add_argument("--n", type=int, default=200)
p.add_argument("--concurrency", type=int, default=16)
p.add_argument("--max-tokens", type=int, default=256)
asyncio.run(main(p.parse_args()))
