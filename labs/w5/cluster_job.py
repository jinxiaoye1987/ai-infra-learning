"""连接到已启动的本地集群（ray start --head），提交一批任务后保留一个 Actor 以便观察。"""
import time

import ray

ray.init(address="auto")          # 连接现有集群，而不是在脚本里新建一个


@ray.remote
def work(i):
    time.sleep(0.2)
    return i


@ray.remote
class Keeper:
    def ping(self):
        return "ok"


ray.get([work.remote(i) for i in range(40)])
k = Keeper.options(name="keeper", lifetime="detached").remote()   # 具名、脱离 Driver 存活的 Actor
print(ray.get(k.ping.remote()))
