"""实验 4：容错——Task 自动重试、应用异常、Actor 重启。"""
import os
import time

import ray

ray.init(num_cpus=2, include_dashboard=False)


MARK = "/tmp/ray_flaky_{}"
for i in range(6):
    if os.path.exists(MARK.format(i)):
        os.remove(MARK.format(i))


@ray.remote(max_retries=3)
def flaky(i):
    if i % 2 == 0 and not os.path.exists(MARK.format(i)):
        open(MARK.format(i), "w").close()
        os._exit(1)                 # 偶数号任务第一次执行时让 worker 进程崩溃（类似 executor 丢失）
    return i, os.getpid()


print("进程崩溃会被自动重试:", ray.get([flaky.remote(i) for i in range(6)]))


@ray.remote
def bad():
    raise ValueError("脏数据")      # 应用层异常：默认不重试，异常抛回 Driver


try:
    ray.get(bad.remote())
except ray.exceptions.RayTaskError as e:
    print("应用异常传回 Driver:", type(e).__name__, "|", str(e).splitlines()[-1])


@ray.remote(max_restarts=1)          # 进程挂了允许重启 1 次；方法调用默认不重试
class Svc:
    def __init__(self):
        self.calls = 0

    def ping(self):
        self.calls += 1
        return self.calls, os.getpid()

    def die(self):
        os._exit(1)


s = Svc.remote()
print("重启前:", ray.get(s.ping.remote()), ray.get(s.ping.remote()))
s.die.remote()
for _ in range(20):                  # 重启需要一点时间，期间调用会失败
    try:
        print("重启后（状态丢失、pid 变化）:", ray.get(s.ping.remote()))
        break
    except ray.exceptions.RayActorError as e:
        print("调用失败:", type(e).__name__)
        time.sleep(0.5)
