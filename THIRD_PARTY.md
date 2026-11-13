# 第三方材料

本文件记录当前树里能直接对应到上游的材料。许可名称来自本仓库已有的锁文件字段，或来自该作品作者公布的文本。没有看到许可文本的，不在这里补写一个许可名称。

本仓库的 MIT 许可不重新授权这些材料。

## 站点直接依赖

版本和许可字段抄自 `site/package-lock.json`（锁文件版本 3，核对日期 2026-11-13）：

| 包 | 锁定版本 | 锁文件中的 license 字段 |
|---|---|---|
| marked | 12.0.2 | MIT |
| mermaid | 11.17.2 | MIT |
| highlight.js | 11.12.0 | BSD-3-Clause |
| puppeteer-core | 25.14.0 | Apache-2.0 |
| wrangler | 3.114.17 | MIT OR Apache-2.0 |

传递依赖各自保留 `site/package-lock.json` 和包内的许可。`node_modules/` 不提交。`node build.js` 会把 `mermaid` 的浏览器脚本复制到 `site/dist/assets/`，`dist/` 也不提交。

## 课程中的引用

周页里的命令、参数和概念说明，有的来自 Ray、vLLM、SGLang、Kubernetes、Kueue、Volcano、KubeRay、NVIDIA GPU Operator、PyTorch、nanoGPT、MLflow 等项目的公开文档或仓库。页面中的链接是出处。这些摘录仍归原作者所有，本文件不逐一改写它们的许可。

公开案例和书目中的作者姓名保留，用于指向原文，不是本仓库维护者的身份。

## 第 19 周适配器文件

`labs/w19/adapter-r4/` 与 `labs/w19/adapter-r16/` 里的 `adapter_config.json` 由 PEFT 0.21.2 写出，`base_model_name_or_path` 为 `Qwen/Qwen2.5-0.5B`。同目录的 `README.md` 是 PEFT 生成的模型卡模板，其中 License 一栏仍是模板原句 “More Information Needed”。该占位句不是本仓库作出的许可承诺。

当前树不包含 `*.safetensors` 权重，也不包含 `mlruns/`。基座模型的使用条件以其作者在模型卡上的说明为准。本仓库不转述、也不代为授予该模型的许可。复现步骤见 `labs/w19/ARTIFACTS.md`。

## 图片

`shots/` 是本站界面截图。`site/static/img/ttft_vs_concurrency.png` 与 `labs/w23/ttft_vs_concurrency.png` 是 `labs/w23/make_chart.py` 从实验指标画出的图。第三方产品的名称和商标仍归权利人。

## 行为准则文本

`CODE_OF_CONDUCT.md` 采用 Contributor Covenant 2.1 的公布译文。贡献者公约文本由其作者以 CC BY 4.0 提供，只覆盖该行为准则文件。
