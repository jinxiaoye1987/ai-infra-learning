"""从 FineWeb 的 sample-10BT 子集流式抽取 5 万条，存成 5 个 Parquet 文件（模拟多文件原始数据）。"""
import pathlib
import time

import pyarrow as pa
import pyarrow.parquet as pq
from datasets import load_dataset

N, FILES = 50_000, 5
out = pathlib.Path("raw")
out.mkdir(exist_ok=True)
t = time.time()
ds = load_dataset("HuggingFaceFW/fineweb", name="sample-10BT", split="train", streaming=True)
rows = []
for r in ds:
    rows.append({"id": r["id"], "url": r["url"], "text": r["text"], "language_score": r["language_score"]})
    if len(rows) == N:
        break
per = N // FILES
for i in range(FILES):
    pq.write_table(pa.Table.from_pylist(rows[i * per:(i + 1) * per]), out / f"part-{i}.parquet")
size = sum(f.stat().st_size for f in out.glob("*.parquet"))
print(f"写出 {N} 条到 {FILES} 个文件，共 {size / 2**20:.1f} MiB，用时 {time.time() - t:.0f}s")
print("字段:", list(rows[0].keys()))
print("示例:", rows[0]["url"], "|", rows[0]["text"][:80].replace("\n", " "))
