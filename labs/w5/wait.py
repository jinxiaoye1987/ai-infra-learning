"""实验 6：ray.wait——谁先完成先处理，应对长尾任务。"""
import random
import time

import ray

ray.init(num_cpus=4, include_dashboard=False)


@ray.remote
def job(i):
    d = 3.0 if i == 0 else random.uniform(0.1, 0.5)   # 0 号是“长尾”任务
    time.sleep(d)
    return i, round(d, 2)


random.seed(1)
t = time.time()
pending = [job.remote(i) for i in range(8)]
while pending:
    done, pending = ray.wait(pending, num_returns=1)
    print("%.1fs 完成" % (time.time() - t), ray.get(done[0]))
