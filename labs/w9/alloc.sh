#!/usr/bin/env bash
# 每个节点已分配的 GPU（等价于 kubectl describe node 里的 Allocated resources）
for n in gpu-node-0 gpu-node-1; do
  printf "%-11s " $n; kubectl describe node $n | grep -E "^\s+nvidia.com/gpu" | tail -1 | awk '{print "已分配 "$2" / 总量 '"$(kubectl get node $n -o jsonpath='{.status.allocatable.nvidia\.com/gpu}')"'"}'
done
