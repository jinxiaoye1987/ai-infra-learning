"""混合精度 + Adam 训练的每卡显存估算（不含激活）。口径：每参数 2(bf16 参数) + 2(bf16 梯度) + 12(fp32 主参数+动量+方差) = 16 字节。
用法：python zero_mem.py --params 7e9 --gpus 8"""
import argparse
p = argparse.ArgumentParser(); p.add_argument("--params", type=float, default=7e9); p.add_argument("--gpus", type=int, default=8)
a = p.parse_args(); P, N = a.params, a.gpus
P_, G_, O_ = 2 * P, 2 * P, 12 * P
rows = [("DP（无分片）", P_ + G_ + O_), ("ZeRO-1（切优化器）", P_ + G_ + O_ / N),
        ("ZeRO-2（再切梯度）", P_ + (G_ + O_) / N), ("ZeRO-3 / FSDP（再切参数）", (P_ + G_ + O_) / N)]
print(f"模型 {P/1e9:g}B 参数，{N} 卡；参数 {P_/1e9:.0f}GB + 梯度 {G_/1e9:.0f}GB + 优化器 {O_/1e9:.0f}GB = {(P_+G_+O_)/1e9:.0f}GB")
for name, b in rows: print(f"{name:<22} 每卡 {b/1e9:7.1f} GB")
