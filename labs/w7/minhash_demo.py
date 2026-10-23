"""MinHash 与 LSH 的原理演示：Jaccard 真值 vs MinHash 估计，以及 band/row 的 S 曲线。"""
import re

from datasketch import MinHash

def shingles(text: str, n: int = 5) -> set:
    w = re.findall(r"\w+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(max(1, len(w) - n + 1))}

a = ("Ray Data is a scalable data processing library for ML and AI workloads built on Ray. "
     "It provides flexible and performant APIs for distributed data processing such as batch inference, "
     "data preprocessing and ingest for ML training.")
b = a.replace("scalable", "highly scalable").replace("such as batch inference", "including offline batch inference")
c = "Apache Spark is a multi-language engine for executing data engineering, data science, and machine learning on single-node machines or clusters."

def mh(s, num_perm):
    m = MinHash(num_perm=num_perm, seed=1)
    for x in s:
        m.update(x.encode())
    return m

sa, sb, sc = shingles(a), shingles(b), shingles(c)
print(f"shingle 数: a={len(sa)} b={len(sb)} c={len(sc)}")
for name, x, y in [("a-b", sa, sb), ("a-c", sa, sc)]:
    true = len(x & y) / len(x | y)
    est = "  ".join(f"k={k}:{mh(x, k).jaccard(mh(y, k)):.3f}" for k in (16, 64, 128, 256))
    print(f"{name} 真实 Jaccard={true:.3f}  MinHash 估计 {est}")

print("\nLSH 候选概率 P = 1-(1-s^r)^b  （num_perm = b*r = 128）")
print("   s   " + "  ".join(f"b={b:>2},r={r:>2}" for b, r in [(32, 4), (16, 8), (8, 16)]))
for s in (0.3, 0.5, 0.7, 0.8, 0.9):
    print(f"  {s:.1f}  " + "  ".join(f"{1 - (1 - s ** r) ** b:>10.3f}" for b, r in [(32, 4), (16, 8), (8, 16)]))
for b, r in [(32, 4), (16, 8), (8, 16)]:
    print(f"b={b},r={r} 阈值近似 (1/b)^(1/r) = {(1 / b) ** (1 / r):.3f}")
