"""博客配图：从第 14 周的真实压测数据画“并发 vs TTFT/吞吐”双轴图（数据从 MLflow 读取，保证图与记录一致）。"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mlflow import MlflowClient
cli = MlflowClient(); exp = cli.get_experiment_by_name("inference-bench")
runs = sorted(cli.search_runs([exp.experiment_id]), key=lambda r: int(r.data.params["concurrency"]))
c = [int(r.data.params["concurrency"]) for r in runs]
ttft = [r.data.metrics["ttft_p95_ms"] / 1000 for r in runs]; tput = [r.data.metrics["throughput_tok_s"] for r in runs]
fig, ax = plt.subplots(figsize=(6, 3.5)); ax2 = ax.twinx()
ax.plot(c, ttft, "o-", color="tab:red", label="TTFT p95 (s)"); ax2.plot(c, tput, "s--", color="tab:blue", label="throughput (tok/s)")
ax.set_xlabel("concurrency"); ax.set_ylabel("TTFT p95 (s)", color="tab:red"); ax2.set_ylabel("throughput (tok/s)", color="tab:blue")
ax2.set_ylim(0, max(tput) * 1.5)
ax.set_title("No batching: throughput flat, TTFT grows (Qwen2.5-0.5B, 8-core CPU)")
fig.tight_layout(); fig.savefig("ttft_vs_concurrency.png", dpi=150)
for x, t, p in zip(c, ttft, tput): print(f"并发 {x}: TTFT p95 {t:.2f}s, 吞吐 {p} tok/s")
print("已保存 ttft_vs_concurrency.png")
