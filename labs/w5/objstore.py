"""实验 3：Object Store——按引用传递、零拷贝读取、“广播变量”。"""
import time

import numpy as np
import ray

ray.init(num_cpus=4, include_dashboard=False)

arr = np.random.default_rng(0).random(25_000_000)          # 200 MB 的 float64 数组
print("数组大小 %.0f MB" % (arr.nbytes / 2**20))


@ray.remote
def col_sum(a, i):
    return float(a[i::8].sum())


# ① 直接把大数组当参数传给 8 个任务：Ray 会为“每次调用”各序列化放入一次 Object Store
t = time.time()
ray.get([col_sum.remote(arr, i) for i in range(8)])
print("按值传 8 次: %.2fs" % (time.time() - t))

# ② 先 ray.put 一次，再传引用：只存一份，各 worker 通过共享内存读取
t = time.time()
ref = ray.put(arr)
ray.get([col_sum.remote(ref, i) for i in range(8)])
print("put 一次 + 传引用: %.2fs" % (time.time() - t))

# ③ 零拷贝：worker 拿到的 numpy 数组是只读的共享内存视图
@ray.remote
def try_write(a):
    try:
        a[0] = 1.0
        return "可写"
    except ValueError as e:
        return f"只读: {e}"

print(ray.get(try_write.remote(ref)))
