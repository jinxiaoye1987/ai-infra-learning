"""实验 1：Task 并行与资源声明。"""
import time

import ray

ray.init(num_cpus=4, include_dashboard=False)
print("集群资源:", ray.cluster_resources())


@ray.remote
def square(x):
    time.sleep(0.5)          # 模拟 0.5 秒的计算
    return x * x


t = time.time()
refs = [square.remote(i) for i in range(16)]   # 立即返回 ObjectRef，不阻塞
print("提交 16 个任务用时 %.3fs，拿到的是:" % (time.time() - t), refs[0])
print("结果:", ray.get(refs), "总用时 %.1fs" % (time.time() - t))


@ray.remote(num_cpus=2)       # 每个任务声明占 2 个 CPU
def square2(x):
    time.sleep(0.5)
    return x * x


t = time.time()
ray.get([square2.remote(i) for i in range(16)])
print("num_cpus=2 时 16 个任务总用时 %.1fs" % (time.time() - t))

# 任务可以嵌套、可以把 ObjectRef 当参数传给下一个任务（Ray 自动等待依赖）
@ray.remote
def add(a, b):
    return a + b

r = add.remote(square.remote(3), square.remote(4))   # 构成一个小 DAG
print("DAG 结果 3²+4² =", ray.get(r))
