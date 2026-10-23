"""实验 1：用 Ray Data 读多文件 Parquet，看 Dataset / block / schema / 惰性执行。"""
import time

import ray

ray.init(num_cpus=4, include_dashboard=False)
ds = ray.data.read_parquet("dirty/")            # 只建执行计划，不读数据
print(ds)                                       # 打印逻辑计划
print("schema:", ds.schema())
t = time.time()
print("行数:", ds.count(), " 用时 %.2fs（count 可直接用 Parquet 元数据）" % (time.time() - t))

mat = ds.materialize()                          # 真正执行，把结果固化在 Object Store
print("物化后 block 数:", mat.num_blocks(), " 总字节 %.1f MiB" % (mat.size_bytes() / 2**20))
row = mat.take(1)[0]
print("一行样例:", {k: (v[:60] + "…" if isinstance(v, str) and len(v) > 60 else v) for k, v in row.items()})
