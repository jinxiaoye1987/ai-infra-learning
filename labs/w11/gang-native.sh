#!/usr/bin/env bash
# 与第 9 周实验 6 相同的两个作业（各 3 worker × 4 卡，交替提交），
# 区别：每个作业先创建一个 K8s 原生 PodGroup（gang 策略，minCount=3），worker 通过 spec.schedulingGroup 加入。
# 需要 K8s v1.37+，并开启 GenericWorkload 特性门控与 scheduling.k8s.io/v1beta1 API。
for j in a b; do
kubectl apply -f - >/dev/null <<YAML
apiVersion: scheduling.k8s.io/v1beta1
kind: PodGroup
metadata: {name: job-$j}
spec:
  schedulingPolicy:
    gang: {minCount: 3}     # 3 个 worker 要么一起调度，要么都不调度
YAML
done
for i in 0 1 2; do
  for j in a b; do
kubectl apply -f - >/dev/null <<YAML
apiVersion: v1
kind: Pod
metadata: {name: job-$j-worker-$i, labels: {job: job-$j}}
spec:
  schedulingGroup: {podGroupName: job-$j}
  tolerations: [{key: nvidia.com/gpu, operator: Exists, effect: NoSchedule}]
  containers:
  - {name: worker, image: busybox, resources: {limits: {nvidia.com/gpu: 4}}}
YAML
  done
done
