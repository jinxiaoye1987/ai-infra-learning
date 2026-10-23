#!/usr/bin/env bash
# 在 KWOK 集群外以普通进程运行 Kueue（本站无 Docker 的变通做法）
export PATH=~/.local/bin:$PATH
KC=${1:-$HOME/.kwok/clusters/lab2/kubeconfig.yaml}
pkill -f kueue-manager; sleep 1
kubectl --kubeconfig $KC apply --server-side -f ~/kueue-run/crds/ >/dev/null
kubectl --kubeconfig $KC wait --for condition=established crd --all --timeout=60s >/dev/null
kubectl --kubeconfig $KC create ns kueue-system 2>/dev/null
KUEUE_METRICS_CERT_DIR=$HOME/kueue-run/certs POD_NAMESPACE=kueue-system nohup kueue-manager \
  --config ~/kueue-run/config.yaml --kubeconfig $KC --feature-gates=VisibilityOnDemand=false --zap-log-level=5 > ~/kueue-run/manager.log 2>&1 &
sleep 10
kubectl --kubeconfig $KC apply -f ~/kueue-run/webhooks.yaml >/dev/null
