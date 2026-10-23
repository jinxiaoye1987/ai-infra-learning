"""比较三种 KV Cache 分配方式的显存利用率（只做记账，不做计算）：
  contiguous：每个请求按 max_len 预留连续空间（早期系统做法）
  paged：按 block（16 token）按需分配，只有最后一个 block 有内部碎片
  paged+prefix：所有请求共享同一段 system prompt 的完整 block
"""
import random, argparse
p = argparse.ArgumentParser()
p.add_argument("--n", type=int, default=64); p.add_argument("--max-len", type=int, default=4096)
p.add_argument("--block", type=int, default=16); p.add_argument("--sys", type=int, default=512)
p.add_argument("--seed", type=int, default=0)
a = p.parse_args(); random.seed(a.seed)
# 某一时刻的 n 个在途请求：system prompt + 用户输入 + 已生成的 token
lens = [a.sys + random.randint(50, 1500) + random.randint(1, 800) for _ in range(a.n)]
used = sum(lens)
ceil = lambda x: -(-x // a.block)
contig = a.n * a.max_len
paged = sum(ceil(l) for l in lens) * a.block
shared = (a.sys // a.block) * a.block                     # 可共享的完整 block 部分
paged_pref = shared + sum(ceil(l - shared) for l in lens) * a.block
print(f"{a.n} 个在途请求，实际 token 数 {used:,}（平均 {used//a.n}）")
for name, alloc in [("contiguous(按 max_len 预留)", contig), ("paged(block=%d)" % a.block, paged),
                    ("paged + 共享 %d token 前缀" % a.sys, paged_pref)]:
    print(f"{name:<28} 分配 {alloc:>9,} token 槽位，逻辑token/物理槽位 {used/alloc:6.1%}，"
          f"同样显存可多容纳 {contig/alloc:4.1f}× 请求")
