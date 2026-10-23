#!/usr/bin/env bash
# 查看 Kueue 工作负载、队列用量与 Pod 分布
echo "--- workloads"; kubectl get workloads.kueue.x-k8s.io -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.ownerReferences[0].name,PRIO:.spec.priority,ADMITTED:.status.conditions[?\(@.type==\"Admitted\"\)].status,FLAVOR:.status.admission.podSetAssignments[0].flavors.nvidia\\.com/gpu,EVICTED:.status.conditions[?\(@.type==\"Evicted\"\)].reason --sort-by=.metadata.creationTimestamp
echo "--- clusterqueues"; kubectl get clusterqueue -o custom-columns=NAME:.metadata.name,PENDING:.status.pendingWorkloads,ADMITTED:.status.admittedWorkloads
for cq in cq-team-a cq-team-b; do echo -n "$cq GPU 用量: "; kubectl get clusterqueue $cq -o jsonpath='{range .status.flavorsUsage[*]}{.name}={.resources[?(@.name=="nvidia.com/gpu")].total}(借用 {.resources[?(@.name=="nvidia.com/gpu")].borrowed}) {end}'; echo; done
echo "--- pods"; kubectl get pods -A -l batch.kubernetes.io/job-name --no-headers -o custom-columns=NS:.metadata.namespace,POD:.metadata.name,NODE:.spec.nodeName,STATUS:.status.phase 2>/dev/null | sort
