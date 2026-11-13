# AI Infra 学习教程（24 周）

面向有大数据、数据仓库或 Hadoop 背景、准备转向 AI Infra 的读者。课程按周写成可以跟着做的阅读和实验，不是维护者的个人履历。

公开维护者身份只有网名 [jinxiaoye1987](https://github.com/jinxiaoye1987)。

在线站点：<https://learning.speclab.info>

## 项目定位

用大数据里已经熟悉的调度、数据管道和平台治理，对照学习模型、GPU 集群、推理服务和实验管理。每周一页，结构是目标、图解、动手实验和检查清单。CPU 上跑过的实验保留实测输出。需要 GPU、而编写时没有 GPU 的步骤，正文保留「未在本站实测」一类标注，并指向官方文档，不补造运行结果。

## 在线站点

2026-11-13 对本仓库 `cd882dc` 与线上做了抽样，不是部署，也没有改访问控制：

- `https://learning.speclab.info/` 返回 HTTP 200。
- 导航里有 38 个页面，名单与 `site/content` 一致，其中包括第 1 周到第 24 周。
- `/m1w1.html` 返回 308，跳到 `/m1w1`，随后为 HTTP 200。抽查的周页同样是 200。
- 这些响应里没有看到跳到登录页。响应头 `server` 为 `cloudflare`，并带有 `x-robots-tag: noindex`。

这次抽样只说明当时没有被登录墙拦住。访问策略在 Cloudflare 控制台里，可以在仓库之外改变。更早的内部笔记不能当作当前状态。本次不修改 DNS、Access 或 Pages 项目。部署方式见 [docs/cloudflare-pages.md](docs/cloudflare-pages.md)。

## 目录

| 路径 | 作用 |
|---|---|
| `site/content/` | 站点正文，构建时拆成页面。24 周都在这里 |
| `site/new/` | 第 2 周到第 24 周的分周稿。没有 `m1w1.md`，第 1 周写在 `site/content/01-m1.md`，不是缺课 |
| `site/build.js` | Markdown 生成静态页 |
| `site/static/` | 样式、脚本和图片 |
| `labs/w1/` … `labs/w24/` | 各周实验脚本和小样例 |
| `tools/` | 维护者用来拼接正文和参考资料的脚本，预览站点不必运行 |
| `shots/` | 站点界面截图 |
| `docs/` | 部署说明 |

`site/dist/`、`site/node_modules/`、实验原始数据、模型权重和 `mlruns/` 不进入当前树。对应忽略规则在 `.gitignore`。

## 依赖版本

预览站点使用 Node.js。本机验证时是 Node.js 22.23.4、npm 10.9.9。持续集成使用 Node.js 22。`site/package.json` 声明 `node >= 20`。

`site/package-lock.json` 锁定的直接依赖：

| 包 | 锁定版本 | 许可（以锁文件中的记录为准） |
|---|---|---|
| marked | 12.0.2 | MIT |
| mermaid | 11.17.2 | MIT |
| highlight.js | 11.12.0 | BSD-3-Clause |
| puppeteer-core | 25.14.0 | Apache-2.0 |
| wrangler | 3.114.17 | MIT OR Apache-2.0 |

构建页面只用到 marked、mermaid 和 highlight.js。`puppeteer-core` 只给可选的本地 Mermaid 检查使用，持续集成不启动浏览器。`wrangler` 留在依赖里，本次构建和文档都不调用它去部署。

实验脚本没有一份仓库级的 Python 锁定文件。各周「验证说明」里写了当时用过的版本，换环境后以你实际安装的官方版本为准。

## 安装、构建、预览

```bash
cd site
npm ci
npm test
python3 -m http.server 8765 --directory dist
```

浏览器打开 <http://127.0.0.1:8765/>。本地文件名带 `.html`。线上抽样里，带 `.html` 的地址会跳到不带后缀的路径，这个跳转不在本仓库的配置文件里。

`npm test` 会先运行 `node build.js`，再运行 `node check_content.js`，检查 38 个页面是否都在、站内链接是否指向生成结果，以及指定周页是否仍保留「未在本站实测」。

可选的浏览器检查需要本机 Chrome，持续集成不跑：

```bash
cd site
node check_mermaid.js m1w2 m1w3
```

## 课程结构

`site/content` 里现有 38 个页面：4 个开始页、6 个月概览、24 个周页、4 个参考页。周页 slug 是 `m1w1` 到 `m6w4`，没有空号。

| 阶段 | 主题 | 周页 |
|---|---|---|
| 第 1 月 | 模型与训练基础、Tokenizer、注意力与 KV Cache | 第 1–4 周 |
| 第 2 月 | 数据清洗、去重、质量打分（Ray / Spark） | 第 5–8 周 |
| 第 3 月 | Kubernetes 调度、Kueue、Gang、Volcano、KubeRay | 第 9–12 周 |
| 第 4 月 | 推理服务、批处理、前缀复用、量化、Ray Serve | 第 13–16 周 |
| 第 5 月 | 分布式训练（DDP / FSDP / LoRA）、MLflow | 第 17–20 周 |
| 第 6 月 | 容量规划、RAG 流水线、复盘与模拟面试 | 第 21–24 周 |

正文里写的阅读和实验时间大约是每周 8–15 小时，来自原指南和各周页，不是这次重新计时的结果。

`labs/w1` 到 `labs/w24` 目录都在。大体积原始数据不在库里。第 19 周的复现步骤还在 `labs/w19/`，权重和 MLflow 运行目录不在当前树里，说明见 [labs/w19/ARTIFACTS.md](labs/w19/ARTIFACTS.md)。

## 贡献

请先读 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。安全问题走 [SECURITY.md](SECURITY.md)，不要开公开 Issue 贴细节。

## 局限

- 课程会过时。命令、默认参数和招聘链接以对应项目当时的官方文档为准。
- 标注了「未在本站实测」的 GPU 步骤没有配套的本站输出。那些命令按官方文档编写，不能当成已经跑通的结果。
- 本次只整理开源文件，没有重写课程、没有改界面，也没有把某一周缩成摘要。
- 仓库曾经有一份内部进度日志，里面有本机路径、部署记录和当时的访问检查。该文件已从当前树移除。Git 历史没有改写，那些历史记录不代表线上现在的访问状态。
- 历史提交里仍然有已经从当前树删掉的权重和日志文件。克隆旧提交仍可能得到它们。
- 2026-11-13 用当前正文构建后，抽取了 38 个页面的正文纯文本并与线上比较：37 页一致。`lab-env` 只有一处不同，源码里的 `python@3.12` 在线上被 Cloudflare 的邮箱混淆换成了占位文本。这次没有改该命令，也没有改 Cloudflare。抽样不能证明以后的访问策略不变。
- 整理这些开源文件时使用了 AI 辅助。课程正文、实验数字、命令和外部链接都可能有错，使用前请对照官方文档，并用你自己的运行结果核对。

## 许可

原创程序和原创课程文档继续使用仓库里已有的 [MIT 许可](LICENSE)。本次不更换许可文件，也不把这些文档改到另一套许可。

第三方依赖、正文引用的命令和文档、模型、商标，以及他人作品的署名，都不因这份 MIT 许可而被重新授权。边界写在 [NOTICE](NOTICE) 和 [THIRD_PARTY.md](THIRD_PARTY.md)。
