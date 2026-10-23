"""毕业项目 B（多租户推理平台）的容量与成本估算。所有输入都是“假设值”，必须用你自己的压测结果替换。
思路：单卡在满足 SLO 时的最大并发（来自压测表）→ 单卡可承载的请求率（Little 定律）→ 所需卡数 → 成本。"""
import argparse, math
p = argparse.ArgumentParser()
p.add_argument("--peak-qps", type=float, default=20)        # 业务峰值请求率（假设）
p.add_argument("--out-tokens", type=int, default=300)       # 平均输出长度（假设）
p.add_argument("--slo-conc", type=int, default=16)          # 压测中满足 TTFT/TPOT SLO 的最大并发（假设，取自第 14 周表格）
p.add_argument("--tpot-ms", type=float, default=40)         # 该并发下的 TPOT p50（假设）
p.add_argument("--ttft-ms", type=float, default=500)        # 该并发下的 TTFT p50（假设）
p.add_argument("--headroom", type=float, default=0.3)       # 冗余比例：故障、发布、突发
p.add_argument("--price", type=float, default=0.0)          # 每 GPU·小时单价（填写平台实际价格；0 表示不算金额）
p.add_argument("--teams", default="A:0.6,B:0.4")            # 各团队流量占比（用于 Kueue 配额）
a = p.parse_args()
e2e = a.ttft_ms / 1000 + (a.out_tokens - 1) * a.tpot_ms / 1000            # 单请求端到端时间
per_gpu_qps = a.slo_conc / e2e                                            # Little 定律：L = λW → λ = L / W
gpus = math.ceil(a.peak_qps / per_gpu_qps * (1 + a.headroom))
print(f"单请求 E2E = {a.ttft_ms/1000:.2f} + {a.out_tokens-1}×{a.tpot_ms/1000:.3f} = {e2e:.1f}s")
print(f"单卡在 SLO 内的并发 {a.slo_conc} → 可承载 {per_gpu_qps:.2f} 请求/s（{per_gpu_qps*a.out_tokens:.0f} 输出 token/s）")
print(f"峰值 {a.peak_qps} 请求/s，冗余 {a.headroom:.0%} → 需要 {gpus} 张卡")
quota = {t: math.ceil(gpus * float(s)) for t, s in (x.split(":") for x in a.teams.split(","))}
print("Kueue nominalQuota 建议（按流量占比向上取整，余量放进 cohort 共享）：", quota)
hours = gpus * 24 * 30
print(f"每月 GPU·小时 = {gpus}×24×30 = {hours:,}" + (f"，约 {hours*a.price:,.0f}（单价 {a.price}/GPU·小时）" if a.price else "（未填写单价）"))
