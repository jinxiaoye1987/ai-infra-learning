"""看清 Parquet 文件的内部结构，并验证“列裁剪”和“谓词下推”。"""
import os
from datetime import datetime
import time

import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq

f = pq.ParquetFile("events.parquet")
md = f.metadata
print(f"CSV {os.path.getsize('events.csv') / 2**20:.1f} MiB vs "
      f"Parquet {os.path.getsize('events.parquet') / 2**20:.1f} MiB")
print(f"行数={md.num_rows:,} 行组数={md.num_row_groups} 列数={md.num_columns}")
print(f.schema_arrow)

rg = md.row_group(0)
print(f"\n第 0 个行组：{rg.num_rows:,} 行")
for i in range(rg.num_columns):
    c = rg.column(i)
    s = c.statistics
    print(f"  {c.path_in_schema:8s} {c.compression:5s} 压缩后 {c.total_compressed_size / 1024:7.1f} KiB "
          f"解压后 {c.total_uncompressed_size / 1024:7.1f} KiB  编码 {c.encodings}  "
          f"min={s.min} max={s.max}")

print("\n每个行组 ts 的 [min, max]：")
for i in range(md.num_row_groups):
    s = md.row_group(i).column(2).statistics
    print(f"  rg{i}: {s.min} ~ {s.max}")


def bench(label, fn, repeat=5):
    best = min((lambda t: (fn(), time.perf_counter() - t)[1])(time.perf_counter()) for _ in range(repeat))
    print(f"{label:34s} {best * 1000:7.1f} ms")


print("\n--- 列裁剪（只读需要的列） ---")
bench("读全部 4 列", lambda: pq.read_table("events.parquet"))
bench("只读 user_id, event", lambda: pq.read_table("events.parquet", columns=["user_id", "event"]))

print("\n--- 谓词下推（按行组统计信息跳过） ---")
dset = ds.dataset("events.parquet")
lo, hi = datetime(2026, 1, 10), datetime(2026, 1, 11)
flt = (pc.field("ts") >= lo) & (pc.field("ts") < hi)   # WHERE ts >= '2026-01-10' AND ts < '2026-01-11'
frags = list(dset.get_fragments())
kept = [p.row_groups[0].id for fr in frags for p in fr.split_by_row_group(flt)]
print(f"过滤 2026-01-10 当天：{md.num_row_groups} 个行组里只需读 {len(kept)} 个 -> {kept}")
bench("全表读再过滤", lambda: pq.read_table("events.parquet").filter(flt))
bench("filters= 下推", lambda: pq.read_table("events.parquet", filters=flt))
print("下推结果行数:", pq.read_table("events.parquet", filters=flt).num_rows)
