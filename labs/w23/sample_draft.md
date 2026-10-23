# 从 YARN 容量调度到 Kueue：一个大数据架构师的 GPU 调度笔记

在 YARN 里，我们用队列的 capacity 和 maximum-capacity 管理多团队资源。K8s 默认调度器没有队列概念……

## 实验环境
KWOK 模拟集群（K8s v1.37.1），Kueue v0.20.2 从源码编译。注意：Pod 运行是模拟的，调度决策是实测的。

## 实验：借用与回收
```bash
kubectl apply -f queues.yaml
```
团队 A 提交 3 个作业，第 2 个借用了团队 B 的 A100 额度……团队 B 提交后，Kueue 抢占了借出的作业。

## 局限
KWOK 不运行真实容器，抢占后的训练恢复时间无法在这里测量。
