"""启动 serve_demo，分三个阶段施加负载（并发 2 → 16 → 0），每秒记录副本数与延迟。"""
import asyncio, time, statistics, httpx, ray
from ray import serve
from serve_demo import app

ray.init(num_cpus=8, include_dashboard=False, logging_level="ERROR")
serve.run(app, route_prefix="/", blocking=False)
URL = "http://127.0.0.1:8000/"; lat = []

def replicas():
    st = serve.status().applications["default"].deployments["FakeLLM"]
    return st.replica_states.get("RUNNING", 0), st.replica_states

async def worker(cli, stop):
    while time.time() < stop:
        t = time.perf_counter(); await cli.get(URL); lat.append(time.perf_counter() - t)

async def phase(name, conc, secs):
    global lat; lat = []; stop = time.time() + secs
    async with httpx.AsyncClient(timeout=60) as cli:
        tasks = [asyncio.create_task(worker(cli, stop)) for _ in range(conc)]
        t0 = time.time()
        while time.time() < stop:
            await asyncio.sleep(3); r, states = replicas()
            p50 = statistics.median(lat) if lat else 0
            print(f"[{name}] t={time.time()-t0:4.0f}s 并发={conc:<2} 运行副本={r} 状态={dict(states)} 近期延迟p50={p50*1000:5.0f}ms", flush=True)
            lat = []
        await asyncio.gather(*tasks)

async def main():
    await phase("低负载", 2, 12)
    await phase("高负载", 16, 30)
    await phase("空闲", 0, 30)
asyncio.run(main())
serve.shutdown(); ray.shutdown()
