"""运行任意命令，结束后打印墙钟时间和子进程峰值内存（替代 /usr/bin/time -v）。
用法：python peak.py python train.py ...
"""
import resource
import subprocess
import sys
import time

t = time.perf_counter()
rc = subprocess.call(sys.argv[1:])
dt = time.perf_counter() - t
peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
unit = 2**20 if sys.platform == "darwin" else 2**10   # macOS 单位是字节，Linux 是 KiB
print(f"[peak] 退出码={rc} 用时={dt:.1f}s 峰值内存={peak / unit:.0f} MiB", file=sys.stderr)
sys.exit(rc)
