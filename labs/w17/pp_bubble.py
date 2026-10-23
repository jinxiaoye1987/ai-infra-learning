"""流水线并行的气泡比例：GPipe/1F1B 调度下，p 个 stage、m 个 micro-batch，空闲占比 = (p-1)/(m+p-1)。"""
for p in (2, 4, 8):
    print(f"stage={p}: " + "  ".join(f"m={m}:{(p-1)/(m+p-1):5.1%}" for m in (1, 4, 8, 32)))
