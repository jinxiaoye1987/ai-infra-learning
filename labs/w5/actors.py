"""实验 2：Actor——有状态的常驻进程。"""
import os
import time

import ray

ray.init(num_cpus=4, include_dashboard=False)


@ray.remote
class Counter:
    def __init__(self):
        self.n = 0
        self.pid = os.getpid()

    def add(self, k):
        self.n += k
        return self.n

    def where(self):
        return self.pid


c = Counter.remote()
print("Actor 内方法按提交顺序串行执行:", ray.get([c.add.remote(1) for _ in range(5)]))
print("Actor 进程 pid:", ray.get(c.where.remote()), " Driver pid:", os.getpid())


@ray.remote
class FakeModel:
    """模拟“加载一次模型、反复推理”：构造时慢，每次调用快。"""
    def __init__(self):
        time.sleep(2)                # 假装加载 2 秒权重
        self.w = 3

    def predict(self, batch):
        return [x * self.w for x in batch]


@ray.remote
def predict_task(batch):
    time.sleep(2)                    # Task 每次都要重新“加载模型”
    return [x * 3 for x in batch]


batches = [list(range(i, i + 4)) for i in range(0, 32, 4)]   # 8 个 batch
t = time.time()
ray.get([predict_task.remote(b) for b in batches])
print("用 Task（每次加载模型）处理 8 个 batch: %.1fs" % (time.time() - t))

t = time.time()
pool = [FakeModel.remote() for _ in range(2)]                  # 2 个常驻 Actor
out = ray.get([pool[i % 2].predict.remote(b) for i, b in enumerate(batches)])
print("用 2 个 Actor（各加载一次）处理 8 个 batch: %.1fs，首个结果 %s" % (time.time() - t, out[0]))
