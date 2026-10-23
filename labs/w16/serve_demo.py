"""Ray Serve 自动扩缩容练习：用 CPU 假模型（每请求 0.5s）观察副本数随负载变化。"""
import asyncio
from ray import serve

@serve.deployment(
    ray_actor_options={"num_cpus": 0.5},
    max_ongoing_requests=4,                  # 单副本最多同时处理 4 个请求（类比引擎的 max-num-seqs）
    autoscaling_config={
        "min_replicas": 1, "max_replicas": 6,
        "target_ongoing_requests": 2,        # 期望每个副本平均 2 个在途请求
        "upscale_delay_s": 3, "downscale_delay_s": 10,
        "metrics_interval_s": 1, "look_back_period_s": 3,
    })
class FakeLLM:
    async def __call__(self, req):
        await asyncio.sleep(0.5)             # 模拟一次推理
        return {"text": "ok"}

app = FakeLLM.bind()
