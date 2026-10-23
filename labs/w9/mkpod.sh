#!/usr/bin/env bash
# 用法：./mkpod.sh 名字 GPU数 [nodeSelector产品] [命名空间]
name=$1; gpu=$2; product=${3:-}; ns=${4:-default}
sel=""; [ -n "$product" ] && sel="  nodeSelector: {nvidia.com/gpu.product: $product}"
kubectl apply -n "$ns" -f - <<YAML
apiVersion: v1
kind: Pod
metadata: {name: $name}
spec:
$sel
  tolerations: [{key: nvidia.com/gpu, operator: Exists, effect: NoSchedule}]
  containers:
  - {name: main, image: busybox, resources: {limits: {nvidia.com/gpu: $gpu}}}
YAML
