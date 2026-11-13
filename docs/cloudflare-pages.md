# Cloudflare Pages 部署说明

本文只说明已经存在的静态站如何对应到本仓库。本次没有登录 Cloudflare，没有修改 Pages 项目、访问控制、DNS 或缓存，也没有重新部署。

## 已经观察到的情况

- 站点域名是 <https://learning.speclab.info>。
- 2026-11-13 抽样时，响应头 `server` 为 `cloudflare`。
- 仓库里没有 `wrangler.toml`，没有账号标识，也没有 Pages 项目名称。
- `site/package.json` 依赖了 `wrangler` 3.114.17。当前的 `node build.js` 不调用它。请不要为了预览而执行 `wrangler deploy` 或 `wrangler pages deploy`。
- `site/build.js` 会在输出目录写入 `_headers`，内容是全站 `X-Robots-Tag: noindex` 和 `Cache-Control: no-cache`。2026-11-13 线上响应带有 `x-robots-tag: noindex` 和 `cache-control: no-cache`，与这个文件一致。
- 源码和本地预览使用 `/m1w1.html` 这类路径。2026-11-13 线上 `/m1w1.html` 返回 308，目标是 `/m1w1`。仓库里没有这条重定向的配置。
- 同一天把构建结果的正文纯文本与线上 38 页比较，37 页一致。实验环境页源码中的 `python@3.12` 会让 Cloudflare 的邮箱混淆改写线上可见文字。要看原始命令，以本仓库的 `site/content/00-start.md` 为准。

更早的内部笔记里有过部署记录和访问检查。那些笔记已从当前树移除，不能当作线上现在的配置。

## 若以后要发布新版本

以下步骤供维护者以后手工操作。本次不要执行。

1. 在已有的 Cloudflare Pages 项目中确认它连接的是 `jinxiaoye1987/ai-infra-learning`，而不是新开一个项目或新开一个 Git 仓库。
2. 构建根目录设为仓库根。构建命令使用：

   ```bash
   cd site && npm ci && node build.js
   ```

3. 输出目录填 `site/dist`。
4. 不要把 `site/dist`、`node_modules` 或任何令牌提交进 Git。Pages 的令牌只放在 Cloudflare 或 GitHub Actions 的密钥里。本仓库的持续集成没有部署步骤，也不读取密钥。
5. 构建用的 Node.js 选 22，或至少满足 `site/package.json` 里的 `node >= 20`。
6. 发布后单独检查首页、一个周页和 `/assets/style.css`。带 `.html` 的旧链接是否跳转，以 Pages 项目里已有的设置或 `_redirects` 为准。本仓库没有 `_redirects`。
7. 访问控制和自定义域名保持原样，除非另有明确的变更请求。

本地预览不需要 Cloudflare 账号：

```bash
cd site
npm ci
node build.js
python3 -m http.server 8765 --directory dist
```
