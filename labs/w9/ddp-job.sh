#!/usr/bin/env bash
# 模拟两个分布式训练作业同时到达：每个作业 3 个 worker × 4 卡，worker 交替提交。
# 训练必须等同一作业的 worker 全部到齐才能开始。
# （KWOK 默认会让 Job 管理的 Pod 立即“完成”，所以这里直接建 Pod，相当于 PyTorchJob/RayCluster 控制器创建的 worker）
for i in 0 1 2; do
  for j in a b; do
kubectl apply -f - >/dev/null <<YAML
apiVersion: v1
kind: Pod
metadata: {name: job-$j-worker-$i, labels: {job: job-$j}}
spec:
  tolerations: [{key: nvidia.com/gpu, operator: Exists, effect: NoSchedule}]
  containers:
  - {name: worker, image: busybox, resources: {limits: {nvidia.com/gpu: 4}}}
YAML
  done
done
