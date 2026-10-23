"""实验 5：用 Task 手写一个 MapReduce 词频统计（map → shuffle → reduce）。"""
import collections
import re
import time
import zlib

import ray

ray.init(num_cpus=4, include_dashboard=False)
R = 4                                    # reducer 个数（相当于 shuffle 分区数）

docs = ["the quick brown fox", "the lazy dog", "Ray and Spark", "the fox and the dog"] * 25_000


@ray.remote(num_returns=R)
def mapper(lines):
    parts = [collections.Counter() for _ in range(R)]
    for line in lines:
        for w in re.findall(r"\w+", line.lower()):
            parts[zlib.crc32(w.encode()) % R][w] += 1   # 本地先聚合（combiner），再按稳定哈希分区
    return parts


@ray.remote
def reducer(*parts):
    total = collections.Counter()
    for p in parts:
        total.update(p)
    return total


t = time.time()
chunks = [docs[i::8] for i in range(8)]                      # 8 个 map 分片
map_out = [mapper.remote(c) for c in chunks]                 # 每个返回 R 个 ObjectRef
reduced = [reducer.remote(*[m[r] for m in map_out]) for r in range(R)]
outs = ray.get(reduced)
keys = [set(c) for c in outs]
print("各 reducer 的 key 是否互不重叠:", all(not (keys[i] & keys[j]) for i in range(R) for j in range(i + 1, R)))
result = collections.Counter()
for c in outs:
    result.update(c)
print("Top5:", result.most_common(5), "用时 %.2fs" % (time.time() - t))
