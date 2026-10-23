"""静态 batch vs continuous batching 的离散步进模拟。
模型：每个 decode 步耗时 t = base + per_seq × batch（decode 访存受限，batch 增大时单步耗时增长很慢）；
prefill 简化为把请求的首 token 计入加入后的第一步。请求输出长度长短不一（长尾）。"""
import random, argparse, statistics
p = argparse.ArgumentParser()
p.add_argument("--n", type=int, default=256); p.add_argument("--batch", type=int, default=32)
p.add_argument("--base", type=float, default=20.0); p.add_argument("--per-seq", type=float, default=0.3)
p.add_argument("--seed", type=int, default=0)
a = p.parse_args(); random.seed(a.seed)
outs = [int(random.paretovariate(1.5) * 40) for _ in range(a.n)]   # 输出长度：多数短、少数很长
outs = [min(o, 2000) for o in outs]

def run(continuous):
    queue = list(range(a.n)); active = {}; t = 0.0; done = {}; steps = 0; slot_steps = 0
    while queue or active:
        if continuous or not active:                    # 静态：整批结束才补；连续：每步都补
            while queue and len(active) < a.batch:
                i = queue.pop(0); active[i] = outs[i]
        t += a.base + a.per_seq * len(active); steps += 1; slot_steps += a.batch
        for i in list(active):
            active[i] -= 1
            if active[i] <= 0: done[i] = t; del active[i]
    lat = list(done.values())
    return t, sum(outs) / t * 1000, statistics.mean(lat), sorted(lat)[int(.99 * len(lat))], sum(outs) / slot_steps

print(f"{a.n} 个请求同时到达，输出长度 p50={statistics.median(outs)} 均值={statistics.mean(outs):.0f} 最大={max(outs)}，batch 上限 {a.batch}")
for name, c in [("静态 batch", False), ("continuous batching", True)]:
    t, thr, mlat, p99, occ = run(c)
    print(f"{name:<20} 总耗时 {t/1000:6.1f}s 吞吐 {thr:7.1f} tok/s 平均完成时间 {mlat/1000:6.1f}s p99 {p99/1000:6.1f}s 槽位利用率 {occ:5.1%}")
