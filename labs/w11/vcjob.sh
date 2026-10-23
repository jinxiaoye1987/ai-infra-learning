#!/usr/bin/env bash
# 用法：./vcjob.sh 名字 worker数 每worker卡数 [队列]
# 提交一个 Volcano Job：minAvailable=worker 数，即 gang 调度（全有或全无）
name=$1; n=$2; gpu=$3; q=${4:-default}
kubectl apply -f - <<YAML
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata: {name: $name}
spec:
  schedulerName: volcano
  queue: $q
  minAvailable: $n                 # gang：至少 $n 个 Pod 能同时调度才开始
  tasks:
  - name: worker
    replicas: $n
    template:
      metadata:
        annotations:              # 仅 KWOK：让 Pod 模拟运行 10 分钟
          pod-complete.stage.kwok.x-k8s.io/delay: "600s"
          pod-complete.stage.kwok.x-k8s.io/jitter-delay: "600s"
      spec:
        restartPolicy: Never
        tolerations: [{key: nvidia.com/gpu, operator: Exists, effect: NoSchedule}]
        containers:
        - {name: worker, image: busybox, resources: {limits: {nvidia.com/gpu: $gpu}}}
YAML
