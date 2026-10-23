#!/usr/bin/env bash
# 用法：./job.sh 命名空间 名字 worker数 每worker卡数 运行秒数 [优先级类]
# 生成一个提交到 Kueue LocalQueue “lq” 的分布式训练 Job。
ns=$1; name=$2; n=$3; gpu=$4; secs=$5; prio=${6:-}
plabel=""; [ -n "$prio" ] && plabel="    kueue.x-k8s.io/priority-class: $prio"
kubectl apply -n "$ns" -f - <<YAML
apiVersion: batch/v1
kind: Job
metadata:
  name: $name
  labels:
    kueue.x-k8s.io/queue-name: lq      # 关键：提交到哪个 LocalQueue
$plabel
spec:
  parallelism: $n
  completions: $n
  completionMode: Indexed
  template:
    metadata:
      annotations:
        pod-complete.stage.kwok.x-k8s.io/delay: "${secs}s"          # 仅 KWOK：模拟训练运行 $secs 秒
        pod-complete.stage.kwok.x-k8s.io/jitter-delay: "${secs}s"
    spec:
      restartPolicy: Never
      containers:
      - name: worker
        image: busybox
        resources:
          requests: {cpu: "8", memory: 64Gi}
          limits: {nvidia.com/gpu: $gpu}
YAML
