# 重写进度（gold standard = m1w1）

工作方式：新周内容写在 site/new/<slug>.md → `python3 tools/splice.py <slug>...` 拼进 content；
新参考资料写 JSON → `python3 tools/add_refs.py x.json` → `python3 tools/regen_resources.py`；
`node build.js`；mermaid 检查：dist 上起 `python3 -m http.server 8765` 后 `node check_mermaid.js m1w2 ...`。
实验 venv：/workspace/m1lab/.venv（Py 3.12.15, torch 2.14.1+cpu, transformers 5.20.2）；nanoGPT 克隆在 /workspace/m1lab/nanoGPT。
机器：无 docker、无 GPU、16GB RAM（可用约 6GB）。

## 已完成
- [x] 实验环境页改为 Python 3.12（00-start.md lab-env）
- [x] 第 1 月：m1w2 / m1w3 / m1w4 重写完成，labs/w2 w3 w4，已部署 2026-10-20 10:29 (UTC+8)，部署 d1ec8ef2；登出 curl / 与周页均 302 → Access

## 待办
- [x] 第 2 月：m2w1–m2w4 已 splice、refs 144 行、部署 2026-10-20 11:50 (UTC+8) 884aae58，302 已验证。m2w4 实验4(vLLM) 标未实测
- [x] 第 3 月 m3w1–m3w4（需 kind+docker：本机无 docker → 需标注未实测或另找方案）
- [x] 第 4 月 m4w1–m4w4
- [x] 第 5 月 m5w1–m5w4
- [x] 第 6 月 m6w1–m6w4

## 第 2 月进行中（2026-10-20 10:55 UTC+8）
- m2w1：已写好 site/new/m2w1.md（未 splice），labs/w5 全部实测
- m2w2：labs/w6 实测完成（get_data/make_dirty/explore/clean_ray/clean_funcs/baseline_pandas），正文待写
  关键数字：52500 行脏数据；通过 47451；too_short 2804/non_alpha 1167/avg_word_len 1025/few_stop_words 53；
  Ray 4cpu 11.5s，2cpu 16.8s，1cpu 在 groupby hash shuffle 卡住（90s 超时）；pandas 单进程 17.9s；token 33,414,974
- venv：/workspace/m2lab/.venv（ray 2.59.0）
- 11:50 更新：m2w2.md 写完（输出已按 10:58 重跑实测数字更新）；m2w3.md 写完（labs/w7：minhash_demo/make_neardup/near_jaccard/dedup_ray/dedup_spark，JDK17 在 ~/.local/jdk，pyspark 4.2.0 装在 m2lab）
- m2w4 进行中：labs/w8/edu_score.py（fineweb-edu-classifier CPU，Ray actor 池）。已测 300 篇 maxlen256：1actor×4线程 28.8s；2×2 47.1s；4×1 89.6s；batch1 45.8s；batch64 53.8s；分布 {0:34,1:192,2:56,3:16,4:2}。怀疑 limit 后只有 1 个 block→只 1 个 actor 干活，已加 --blocks/pid 待验证。2000 篇 2×2：644.6s，int>=3 5.9%
- 验证：limit 后默认只 1 actor 干活；--blocks 8 后 4×1 27.4s、2×2 26.8s（4 actors 默认 91.8s）
- 12:xx m2w4.md 写完；开始收尾第 2 月
- 11:55 第 3 月开始：装了 kwokctl v0.8.0 / kubectl v1.37.1 到 ~/.local/bin，尝试 kwok binary runtime
- m3w1：labs/w9 在 KWOK(binary runtime, K8s v1.36.1) 上实测完成（nodes.yaml/gpu-pod/bad-*/quota/mkpod/alloc/ddp-job），正文写作中
- m3w1.md 写完
- m3w1 已 splice（未部署，月末统一部署）
- 12:00 kueue v0.20.2 从源码 go build 成功 ~/.local/bin/kueue-manager（go 1.27.3 在 ~/.local/go），计划 out-of-cluster 运行；KWOK 用 pod-complete.stage.kwok.x-k8s.io/delay 注解控制 Job 运行时长
- 12:03 Kueue out-of-cluster 跑通：改 main.go metrics cert 路径为 env KUEUE_METRICS_CERT_DIR，--feature-gates=VisibilityOnDemand=false，webhook 用 url https://127.0.0.1:19443 (~/kueue-run/webhooks.yaml)。启动命令见 ~/kueue-run
- 12:15 w10 场景 1-3 实测完成（排队/借用/l4 风味回退/回收抢占/优先级抢占），输出在本轮对话中，正文待写
- 12:20 m3w2.md 写完并 splice（labs/w10 含 start-kueue-outofcluster.sh）
- 12:25 w11：K8s 1.37 原生 PodGroup gang（lab2）实测成功：job-a 3/3 调度、job-b 全部 Pending(Unschedulable)；删 a 后 b 调度（见下一条）
- 12:28 Volcano v1.16.0 源码编译 vc-scheduler/vc-controller-manager，集群外运行于 lab2（~/volcano-run，controller 需禁用 jobflow 等控制器）；vcjob gang 实测：vc-a Running 3/3，vc-b Pending/Inqueue
- 12:30 m3w3 done & spliced: native PodGroup gang, Volcano Job/Queue, KubeRay v1.7.1 (built from source, out-of-cluster, --batch-scheduler=volcano) RayCluster gang all real on KWOK lab2. Volcano capability did not block enqueue (noted, not investigated). Next: m3w4 (docs-based, 未实测), then close month 3.
- 12:45 m3w4 done & spliced (docs-based, GPU parts 未实测; KWOK scheduling of vllm.yaml real).
- MONTH 3 DONE: refs +42 (186 rows), resources regenerated, build ok (38 pages), mermaid ok m3w1-4, deployed 276caedb, / and /m3w3.html → 302. Next: month 4 (m4w1…m4w4).
- 12:31 m4w1 done & spliced: labs/w13 kv_budget/paged_sim/batching_sim/kv_cache_cpu all real (CPU). Month-3 bg processes stopped.
- 12:35 m4w2 done & spliced: labs/w14 mini_server/bench/batch_gain real on CPU (0.5B); vLLM parts 未实测.
- 12:38 m4w3 done & spliced: labs/w15 prefix_reuse/quant_cpu real (CPU); SGLang/vLLM tuning 未实测.
- 12:42 m4w4 done & spliced: labs/w16 Ray Serve autoscaling 1→6→1 and Prometheus 3.15.0 binary scraping mini_server real; vLLM+Grafana 未实测.
- 12:43 MONTH 4 DONE: refs +34 (220), build ok, mermaid ok, deployed, 302 verified. Next: month 5.
- 12:45 m5w1 done & spliced: labs/w17 zero_mem/pp_bubble/tp_demo/fsdp_shard real (CPU gloo torchrun).
- 12:47 m5w2 done & spliced: labs/w18 collectives/ring_allreduce/bw_bench real (gloo); nccl-tests 未实测.
- 12:53 m5w3 done & spliced: labs/w19 shard_compare (DDP vs FSDP2 SmolLM2-135M), ft.py LoRA+MLflow real CPU; DeepSpeed multi-GPU 未实测. Note: OOM at bs4x256 documented.
- 12:56 m5w4 done & spliced: labs/w20 MLflow (sqlite labs/mlflow.db) real: 2 LoRA runs, bench runs, registry v2 champion, REST queries.
- 12:57 MONTH 5 DONE: refs +26 (246), build ok, mermaid ok, deployed e0d3be44, 302 verified. Next: month 6.
- 12:59 m6w1 done & spliced: labs/w21 capacity.py real (assumed inputs).
- 13:02 m6w2 done & spliced: labs/w22 pipeline.py real (600 docs, 73.1s, score 97%). GPU/B/C 未实测. milvus.io docs link skipped (403/redirect loop).
- 13:03 m6w3 done & spliced: labs/w23 make_chart (from MLflow) + blog_lint real; build.js now copies static/img to dist/assets/img.
- 13:05 m6w4 done & spliced: labs/w24 mock_interview + questions.json real.
- 2026-10-20 13:06 MONTH 6 CLOSED: refs 258 rows (+12, juejin.cn dropped: no response), build 38 pages, mermaid OK m6w1-4, deployed ce6b0aad, / and /m6w2.html 302. ALL MONTHS 4-6 DONE.
- 2026-10-20 14:06 UI REDESIGN deployed (highlight.js build-time, code figures w/ copy+lang+filename+line numbers, callouts, TOC, dark mode, themed mermaid). shots/ saved.
