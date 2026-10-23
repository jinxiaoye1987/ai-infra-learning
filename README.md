# AI Infra 学习教程（24 周）

面向有大数据 / 数据平台背景、想转入 **AI Infra** 的自学材料。配套站点：[learning.speclab.info](https://learning.speclab.info)。

## 内容结构

| 月份 | 主题 |
|------|------|
| 第 1 月 | 模型与训练基础、Tokenizer、注意力与 KV Cache |
| 第 2 月 | 数据清洗、去重、质量打分（Ray / Spark） |
| 第 3 月 | Kubernetes 调度、Kueue、Gang、Volcano、KubeRay |
| 第 4 月 | 推理服务、批处理、前缀复用、量化、Ray Serve |
| 第 5 月 | 分布式训练（DDP / FSDP / LoRA）、MLflow |
| 第 6 月 | 容量规划、RAG 流水线、复盘与模拟面试 |

每周约 8–12 小时阅读与实验。GPU 相关实验若本机未跑通，文中会标 **未实测**，不捏造结果。

## 仓库布局

- `site/`：静态站点源码（Markdown → `build.js` → `dist/`）
- `labs/`：按周实验脚本与小样例（大体积原始数据不入库）
- `tools/`：拼装正文、参考资料、资源页的辅助脚本
- `shots/`：UI 截图
- `PROGRESS.md`：重写与部署记录

## 本地构建站点

```bash
cd site
npm ci
node build.js
# 预览
python3 -m http.server 8765 --directory dist
```

可选：对指定周页做 Mermaid 检查：

```bash
cd site
node check_mermaid.js m1w2 m1w3   # 示例
```

## 许可

见 [LICENSE](LICENSE)（MIT）。

## 说明

- 站点线上若仍开着 Cloudflare Access，需登录后才能浏览；开源的是本仓库源码，不等于站点已对公网开放。
- 实验依赖各自 `labs/` 目录下的说明；部分路径需要本机 Python / JDK / kubectl 等，见各周正文。
