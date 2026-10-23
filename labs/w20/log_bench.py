# log_bench.py —— 把第 14 周 mini_server 的真实压测结果记录到 MLflow（GPU 上的 vLLM/SGLang 结果用同样方式追加）
import mlflow
mlflow.set_experiment("inference-bench")
# (引擎, 并发, 吞吐 tok/s, TTFT p50 ms, TTFT p95 ms, TPOT p50 ms) —— 数值来自第 14 周实验 2 的真实输出
rows = [("mini_server-cpu", 1, 25.8, 93, 118, 36.0),
        ("mini_server-cpu", 4, 26.6, 6396, 6510, 36.2),
        ("mini_server-cpu", 8, 25.7, 7941, 13456, 38.3)]
for engine, conc, tput, t50, t95, tpot in rows:
    with mlflow.start_run(run_name=f"{engine}-c{conc}"):
        mlflow.log_params({"engine": engine, "concurrency": conc, "model": "Qwen2.5-0.5B-Instruct", "hardware": "8-core CPU"})
        mlflow.log_metrics({"throughput_tok_s": tput, "ttft_p50_ms": t50, "ttft_p95_ms": t95, "tpot_p50_ms": tpot})
print("logged", len(rows), "runs")
