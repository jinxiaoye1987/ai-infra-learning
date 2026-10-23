# 从大数据架构师到 AI Infra 架构师：自学转型指南

> 读者：做过多年 Hadoop / Spark / Hive / 数仓 / 数据平台架构，很久没写代码，想转 AI Infra 架构师；偏好文字和图解资料，不想看视频课。
> 整理时间：2026-10-16。文中链接已于当天逐一检查能否打开（状态码 200）。标注 ⚠️ 的链接会拦截自动化访问检查（返回 403），但用浏览器可以正常打开。招聘链接随时可能下架。

---

## 0. 一句话结论

**最推荐的方向：先做“LLM 数据基础设施（Data for AI）+ AI 计算平台/调度”，再向“推理服务平台”延伸。**
- 这两个方向最能直接用上大数据背景：分布式系统、资源调度、存储、数据湖、平台治理和成本优化。
- 从 YARN 过渡到 K8s、Volcano/Kueue、Slurm、Ray，从 Spark 过渡到 Ray Data，概念上是平移，补上 GPU、模型和推理知识就行。
- 训练框架内核（Megatron 并行策略、CUDA kernel、通信优化）门槛最高，需要较强的 C++/CUDA 和数学基础，不适合作为第一站。可以列为长期深入方向。

---

## 1. AI Infra 有哪些岗位，哪些最适合大数据背景

| 岗位方向 | 主要工作 | 关键技术 | 与大数据背景的匹配度 |
|---|---|---|---|
| **LLM 数据管线 / AI 数据湖（Data for AI）** | 预训练和后训练数据的清洗、去重、过滤、分词，多模态数据管理，离线批量推理，以及样本、特征与知识库建设 | Ray Data、Spark、datatrove、NeMo Curator、Lance/Iceberg、对象存储、JuiceFS | ⭐⭐⭐⭐⭐ 最高。ETL、数据湖和元数据治理的经验几乎可以直接迁移 |
| **GPU 集群调度 / AI 计算平台** | 多租户 GPU 资源池、队列与配额、Gang 调度、抢占、故障自愈、利用率提升 | Kubernetes、NVIDIA GPU Operator、Volcano、Kueue、Slurm、KubeRay、RDMA | ⭐⭐⭐⭐⭐ 很高。和 YARN 队列、资源隔离、混部是同一类问题 |
| **推理 / 模型服务平台** | 部署大模型服务，压测，弹性扩缩，KV Cache 与路由，降低成本 | vLLM、SGLang、KServe、Ray Serve、llm-d、NVIDIA Dynamo | ⭐⭐⭐⭐ 高。在线高并发、SLA 和可观测性经验可以迁移，但要补推理原理 |
| **MLOps / LLMOps 平台** | 实验管理、模型注册、评测流水线、发布、监控 | MLflow、Kubeflow、Airflow、评测与 Trace 工具 | ⭐⭐⭐⭐ 高。和数据开发平台、调度平台很像 |
| **向量数据库 / RAG 平台** | 文档入库流水线、Embedding、向量检索、混合检索、权限 | Milvus、Elasticsearch/OpenSearch、各类 Embedding 模型 | ⭐⭐⭐⭐ 高。可以理解为一种新的“检索型存储 + 数据管道” |
| **训练基础设施（分布式训练框架）** | 数据并行、张量并行、流水线并行、专家并行，显存优化，通信优化，checkpoint | PyTorch FSDP、Megatron-LM、DeepSpeed、NCCL、CUDA | ⭐⭐ 偏低。需要深入 GPU、通信和数学，适合长期深入 |

### 可迁移技能对照表

| 大数据中你熟悉的 | AI Infra 中对应的 |
|---|---|
| YARN 队列、容量调度、资源隔离 | K8s 加 Volcano/Kueue 的队列与配额，Slurm partition，Gang 调度 |
| Spark / MapReduce | Ray（Task/Actor），Ray Data 流式处理与 CPU/GPU 异构 pipeline |
| HDFS / 对象存储 / Alluxio | 用对象存储、JuiceFS、CubeFS 等加缓存来提供训练数据和保存 checkpoint |
| Hive / Iceberg / 数据湖 | 多模态数据湖、样本库、数据版本管理 |
| Flink 实时链路、高并发服务 | 在线推理服务、流式 token 输出、SLA 与限流降级 |
| 集群运维与成本治理 | GPU 利用率治理（MIG/MPS/vGPU）、Spot 实例、混部 |

**公开案例佐证：**
- 美团在 ArchSummit 2023 做过一次分享，题为《大数据及机器学习基础设施云原生改造实践》。分享讲到用 K8s 替代 YARN，并为 GPU 亲和、Gang 调度、抢占和故障恢复补齐能力：https://fxbaogao.com/detail/4646648
- 理想汽车的大数据平台从 Hadoop 迁到云原生，用 JuiceFS 让大数据平台和 AI 平台共享数据（InfoQ）：https://www.infoq.cn/article/yOse9OblQT4zTMl1RaEw
- 字节跳动用 Ray Data 处理 200TB 级多模态离线推理，文中有 Spark BSP 与 Ray 流水线执行的对比：https://www.anyscale.com/blog/how-bytedance-scales-offline-inference-with-multi-modal-llms-to-200TB-data
- Anyscale 对比了 Ray Data、Spark 和 SageMaker 做离线批量推理的表现：https://www.anyscale.com/blog/offline-batch-inference-comparing-ray-apache-spark-and-sagemaker
- Pinterest 把推理任务从 Spark 迁到 Ray，其中一个任务的年成本降到原来的约 1/30 ⚠️：https://medium.com/pinterest-engineering/ray-batch-inference-at-pinterest-part-3-4faeb652e385

---

## 2. 技能差距与 6 个月路线图（每周约 10–15 小时）

### 需要补的能力（按优先级）
1. **Python 编程手感**：重新能写几百行的脚本和服务。可以借助 AI 编程助手，但要读懂它生成的代码。
2. **大模型基本原理**：Transformer、token、KV Cache；训练、微调和推理各自的资源特征，包括显存估算和计算量与带宽的关系。
3. **GPU 与硬件常识**：显存、HBM、NVLink、InfiniBand/RoCE、NCCL 集合通信，以及 MIG。
4. **云原生**：K8s 的 Operator/CRD、调度器、device plugin，GPU Operator。
5. **Ray**：Core、Data、Serve、Train。
6. **推理引擎**：vLLM 和 SGLang 的核心机制，包括 PagedAttention、continuous batching、prefix cache、PD 分离和量化。
7. **分布式训练概念**：DP/TP/PP/EP，ZeRO/FSDP，checkpoint。架构师要做到“懂原理、能评估”，不要求会写 kernel。

### 路线图

**第 1 个月：恢复手感 + 补 LLM 原理**
- 阅读：Datawhale 的 happy-llm（中文，从零讲解 LLM 原理）；Karpathy 的 nanoGPT 代码。
- 项目 1：在 CPU 或一张小 GPU（云上按小时租）上跑通 nanoGPT 的 Shakespeare 小例子，记录显存占用和训练速度。
- 项目 2：用 Python 写一个小脚本，按“参数量 × 精度”估算 7B、70B 模型在训练和推理时分别需要多少显存，并和实测值对照。

**第 2 个月：Ray + LLM 数据管线（发挥大数据优势）**
- 阅读：Ray Data 文档、Ray Data LLM 文档；datatrove 和 NeMo Curator 的 README 及示例。
- 项目 3：用 Ray Data 处理一份公开文本语料（几 GB 即可），包括读 Parquet、清洗、MinHash 去重、质量过滤，最后写回 Parquet。再用 Spark 实现同样的流程，对比两者的代码和执行模型。
- 项目 4：用 `ray.data.llm` 加 vLLM 跑一个小模型，对上万条数据做离线批量打标签或摘要，观察 GPU 利用率。

**第 3 个月：K8s + GPU 调度**
- 阅读：K8s 官方文档中的 GPU 调度部分、NVIDIA GPU Operator、Volcano、Kueue、KubeRay 文档。
- 项目 5：先用 kind 或 minikube 搭 K8s，在没有 GPU 的环境里练 Kueue/Volcano 的队列、配额和 Gang 调度；再租一台 GPU 云主机，装 GPU Operator，跑 vLLM Pod。
- 产出：写一篇“YARN 容量调度 vs Kueue/Volcano”的对比笔记，这也能作为面试材料。

**第 4 个月：推理服务平台**
- 阅读：vLLM 文档和博客、PagedAttention 论文、SGLang 文档、LMSYS 博客、llm-d 与 NVIDIA Dynamo 的 README。
- 项目 6：分别用 vLLM 和 SGLang 部署同一个 7B 量级模型，自己写压测脚本，统计吞吐、TTFT（首 token 延迟）和 TPOT（单 token 生成延迟），并试验调整 batch、max_num_seqs 和量化参数。
- 项目 7：用 KServe 或 Ray Serve 加 Prometheus/Grafana 搭一个带自动扩缩容和监控的推理服务。

**第 5 个月：分布式训练与 MLOps（达到“懂原理”的程度）**
- 阅读：HuggingFace 的 Ultra-Scale Playbook（重点推荐，图文讲解各种并行）、Google 的 *How to Scale Your Model*、stas00 的 ml-engineering、DeepSpeed ZeRO 与 Megatron-LM 的文档。
- 项目 8：在两张 GPU 上分别用 DeepSpeed ZeRO-2/3 或 FSDP 做一次 LoRA 或全参微调，对比显存占用和速度；用 MLflow 记录实验结果。

**第 6 个月：整合作品集 + 求职**
- 毕业项目（三选一）：
  - A. 一个端到端的“LLM 数据平台”：从数据湖读取，经 Ray Data 清洗、去重，再做批量推理和打标签，最后产出带版本的数据集。
  - B. 一个“多租户 GPU 推理平台”：K8s 加 Kueue，配合 vLLM、KServe 和监控，并附成本报表。
  - C. 一个 RAG 平台：文档入库流水线，用 Milvus 做混合检索，加上评测。
- 把项目写成技术博客（知乎或掘金），突出“大数据经验 → AI Infra 问题”的类比。比起代码量，架构师面试更看重这类表达。

> 写代码不熟练的人可以这样起步：先跑通官方示例，然后每次只改一个参数，记下变化，写成笔记。不要一开始就读框架源码。

---

## 3. 文字类学习资源精选

### 书 / 长文教程
- *Designing Data-Intensive Applications*（DDIA，中文版《数据密集型应用系统设计》）：如果已经读过，可以重读其中分布式部分。https://dataintensive.net/
- Chip Huyen 的 *AI Engineering*，配套仓库：https://github.com/chiphuyen/aie-book
- HuggingFace 的 Ultra-Scale Playbook（分布式训练图解）：https://huggingface.co/spaces/nanotron/ultrascale-playbook
- Google DeepMind 的 *How to Scale Your Model*：https://jax-ml.github.io/scaling-book/
- Stas Bekman 的 ml-engineering（训练和推理工程实践大全）：https://github.com/stas00/ml-engineering
- Lilian Weng 的《How to Train Really Large Models on Many GPUs?》：https://lilianweng.github.io/posts/2021-09-25-train-large/
- 中文：Datawhale 的 happy-llm：https://github.com/datawhalechina/happy-llm
- 中文：ZOMI 等人的 AISystem（AI 系统全栈）：https://github.com/chenzomi12/AISystem
- 中文/英文：微软的 AI-System 课程讲义：https://github.com/microsoft/AI-System
- 中文：廖维明《工程师的 AI 学习指南》，作者是大数据工程师出身：https://www.liaoweiming.org/blog/ai-learning-guide-for-engineers

### 关键论文
- vLLM 的 PagedAttention 论文：https://arxiv.org/abs/2309.06180

### 官方文档
- Ray Data：https://docs.ray.io/en/latest/data/data.html
- Ray Data 处理 LLM：https://docs.ray.io/en/latest/data/working-with-llms.html
- vLLM 文档：https://docs.vllm.ai/en/latest/
- K8s GPU 调度：https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/
- Slurm 文档：https://slurm.schedmd.com/documentation.html

### GitHub 仓库（按方向）
- 推理：vLLM https://github.com/vllm-project/vllm ｜ SGLang https://github.com/sgl-project/sglang ｜ llm-d https://github.com/llm-d/llm-d ｜ NVIDIA Dynamo https://github.com/ai-dynamo/dynamo ｜ KServe https://github.com/kserve/kserve
- 计算与调度：Ray https://github.com/ray-project/ray ｜ GPU Operator https://github.com/NVIDIA/gpu-operator ｜ Volcano https://github.com/volcano-sh/volcano ｜ Kueue https://github.com/kubernetes-sigs/kueue ｜ Kubeflow Trainer https://github.com/kubeflow/trainer ｜ 蚂蚁 DLRover https://github.com/intelligent-machine-learning/dlrover
- 训练：DeepSpeed https://github.com/deepspeedai/DeepSpeed ｜ Megatron-LM https://github.com/NVIDIA/Megatron-LM ｜ NCCL https://github.com/NVIDIA/nccl ｜ nanoGPT https://github.com/karpathy/nanoGPT
- 数据：datatrove https://github.com/huggingface/datatrove ｜ NeMo Curator https://github.com/NVIDIA/NeMo-Curator
- MLOps / RAG：MLflow https://github.com/mlflow/mlflow ｜ Milvus https://github.com/milvus-io/milvus

### 持续关注的博客
- vLLM 博客：https://blog.vllm.ai/
- LMSYS / SGLang 博客：https://lmsys.org/blog/
- Anyscale 博客：https://www.anyscale.com/blog
- InfoQ 中文 QCon“下一代 Data for AI 技术架构”专题（字节、Zilliz、JuiceFS、PayPal、OPPO 等公司的分享）：https://www.infoq.cn/article/dx5t48sffpjazwbvspnt

---

## 4. 转型案例与就业市场信号

### 公开转型案例 / 文章
- **廖维明**自述“从大数据工程师逐步转型到 AI Agent 工程和推理优化方向”，给出了“数学 → 模型 → 训练 → 推理 → 工程”的学习路径，并说明哪些大数据能力可以迁移：https://www.liaoweiming.org/blog/ai-learning-guide-for-engineers
- **丁远普**（火山引擎 AI 数据湖研发负责人）：据 InfoQ 介绍，他有 10 年以上大数据 B 端产品研发经验，负责 EMR 和 LAS，从 2023 年开始做 Data for AI 转型探索。https://www.infoq.cn/article/lmg6blihf5yslvwgmzz2
- **长凡**（蚂蚁 DLRover 开源负责人）访谈《走近 AI Infra 架构师》：他从大数据和机器学习入门，后来进入 ML Infra，访谈中谈到架构师如何从训练需求中抽象出 Infra 问题。https://mp.weixin.qq.com/s/2tYO1z5pt-nU6duANzDlbg
- **团队层面的转型**：美团的大数据与 ML 基础设施云原生化（链接见第 1 节）；理想汽车的大数据与 AI 平台数据共享（链接见第 1 节）。
- 英文：ai-system-design-guide 的 TRANSITION_GUIDE，梳理了 Data Engineer 和 Platform Engineer 转型 AI Infra 时的技能差距：https://github.com/ombharatiya/ai-system-design-guide/blob/main/TRANSITION_GUIDE.md

> 说明：没有找到既公开又可验证、以“Hadoop 架构师 → AI Infra 架构师”为题的完整个人长文。以上是能核实的最接近的案例，文中没有编造任何人物。

### 招聘 JD 信号（2026 年抓取，可能下架）
- **阿里巴巴 AI Infra 工程师（计算方向，校招/实习）**：工作内容涵盖十万卡级 GPU 集群、DP/TP/PP/EP 并行、集合通信、统一调度；要求了解 PyTorch、Megatron-LM、DeepSpeed、vLLM、SGLang，以及 NVLink 和 CUDA。https://campus-talent.alibaba.com/campus/position/199904060014
- **西湖数智 Infra 加速（杭州）**：要求 5 年以上基础设施经验；熟悉 Megatron、DeepSpeed、FSDP；懂 PagedAttention 和 Continuous Batching；有 K8s 和 IB/RoCE 经验。https://westlakedi.com/careers/infra
- **仪电智算 AI Infra 工程师（大模型推理平台方向，北京，猎聘）**：要求 3–5 年分布式系统经验；会开发 K8s Operator 和 CRD；有 vLLM/SGLang 调优、Benchmark 体系和可观测性经验。https://www.liepin.com/job/1983042681.shtml
- **Seekr Senior AI Infrastructure Engineer（美国）**：要求生产环境 K8s、GPU 基础设施、分布式推理经验，以及 vLLM、Ray Serve、Triton 和可观测性工具。https://www.seekr.com/careers/?gh_jid=4712814005
- **Inferact MTS, Cloud Orchestration**：要求 K8s Operator 开发、GPU 集群运维、Ray 和 Slurm，以及 vLLM 部署经验。https://jobs.ashbyhq.com/inferact/1f7ff2b3-bcbf-46e3-abcc-ada332250a64

**JD 共性：**
- K8s 和 GPU 调度几乎是必选项。
- 推理方向必须懂 vLLM/SGLang，以及 KV Cache 和 batching。
- 训练方向要求 Megatron/DeepSpeed 加 NCCL/RDMA。
- 资深岗位看重有没有“大规模分布式系统 + 稳定性/成本治理”的落地经验，这正是大数据架构师的优势。
- 要拿出来的证据：GPU 相关的作品（项目 4、5、6），以及能讲清楚原理的博客文章。

---

## 5. 给架构师的几条建议
1. **定位上讲“大数据 + AI Infra”的复合优势**，不要和应届生拼 CUDA。首选数据平台和 AI 平台融合的团队，比如 AI 数据湖、AI 计算平台、推理平台。
2. **内部转岗通常比跳槽更容易**：如果所在公司已有 GPU 集群，可以主动承接“Spark/Flink 与 GPU 混部”“样本数据湖”“离线批量推理”这类交叉项目。
3. **每个项目都记录量化数据**（GPU 利用率、吞吐、成本），架构师面试主要看你对瓶颈的分析和取舍。
4. **持续跟进**：这个领域按月更新，每周花 1 小时读 vLLM、LMSYS、Anyscale 的博客，以及 InfoQ 的 AI Infra 专题。
