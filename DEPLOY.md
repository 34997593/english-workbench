# 英语学习工作台 · 部署与备份说明

## 文件清单
- `english-workbench-mobile.html` —— 主程序（纯静态单页，手机/电脑浏览器直接打开）
- `fetch-news.py` —— 每日真实新闻抓取脚本（Python 标准库，无第三方依赖）
- `.github/workflows/daily-news.yml` —— GitHub Action，每天 UTC 23:00 自动抓新闻并推送 `news.json`
- `news.json` —— 抓取结果（由 Action 自动生成；本地也可手动跑脚本生成）
- `DEPLOY.md` —— 本说明

---

## 一、让真实新闻每天自动更新（推荐：GitHub Action）

1. 在 GitHub 新建一个**公开**仓库（如 `english-news`）。
2. 把本目录这些文件传上去：`english-workbench-mobile.html`、`fetch-news.py`、`.github/` 整个目录。
   （不用传 `news.json` 也行，Action 第一次运行会自动生成。）
3. 仓库 **Settings → Actions → General → Workflow permissions** 选 **Read and write permissions**（workflow 里也已声明 `permissions: contents: write`）。
4. 在 `english-workbench-mobile.html` 里找到常量
   ```js
   const NEWS_JSON_URL="";
   ```
   改成你的 raw 地址：
   ```js
   const NEWS_JSON_URL="https://raw.githubusercontent.com/你的用户名/english-news/main/news.json";
   ```
5. 仓库 **Actions** 标签 → 手动 **Run workflow** 一次，确认生成 `news.json`。
6. 之后每天 **UTC 23:00（北京时间 07:00）** 自动更新，醒来就有新鲜新闻。

> 为什么用 GitHub Action 而不是公共代理：服务端能直连 RSS（无浏览器 CORS 限制），BBC / Al Jazeera / Guardian 在 runner 上都能抓到，比之前那几个被墙的公共 CORS 代理稳得多。

---

## 二、不用 GitHub 也行（纯本地静态）

- **直接双击** `english-workbench-mobile.html` 即可用：内置 10 篇文章 + 点词查义 + 朗读 + 收藏。
- 想有真实新闻：本机跑一次 `python fetch-news.py` 生成 `news.json`，然后**用本地服务器打开**页面：
  ```
  python -m http.server
  ```
  浏览器访问 `http://localhost:8000/english-workbench-mobile.html`
  页面会读同目录的 `news.json`。
  （注意：`file://` 双击方式因浏览器安全限制读不到本地 `news.json`，需走 http 服务器，或填上面的 GitHub raw 地址。）

---

## 三、三层新闻兜底（页面自动按顺序尝试）

1. 同目录 `./news.json`（http 服务器场景）
2. GitHub raw `NEWS_JSON_URL`（file:// 双击但联网场景）
3. 公共代理实时代理（兜底，国内可能不稳）
4. 内置 10 篇文章（最终兜底，永远有内容可读）

---

## 四、学习数据备份（导出 / 导入）

设置弹窗（右上角 ⚙️）里有：
- **⬇ 导出备份**：把收藏、学习进度、设置导出成一个 `.json` 文件。
- **⬆ 导入备份**：选一个之前的备份文件恢复。

换手机 / 清浏览器缓存前记得导出，避免学习记录丢失。
（备份是纯客户端行为，文件只存在你手上，不会上传任何人。）

---

## 五、手动跑抓取脚本

```bash
python fetch-news.py
```
会直连 4 个 RSS 源（能抓到几个算几个），输出 `news.json`。脚本对单个源失败做了容错，不会整体中断。
