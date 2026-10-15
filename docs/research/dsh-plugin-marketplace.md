# DSH 插件市场获取配方（2026-10-15 实证，常备复用）

> 市场=GUI 左下角设置→插件市场，底牌 **npmx.dev（npm 镜像）无策展**——检索即 npm 搜索。

## 1. 检索
    dsh plugin --profile web search <关键词>
（子命令需 --profile；结果含 name/Version/publisher/npmx 链接）

## 2. 安装（若确要装进宿主）
    dsh plugin --profile web add <包名>
    dsh plugin --profile web add github:<owner>/<repo>   # GitHub 直装
装完重启 `dsh web` 生效。**纪律： 分析用途不安装**（装进运行中宿主=污染自舱）。

## 3. 免装取源（分析标准姿势）
    curl -sS https://registry.npmjs.org/<包名> | python3 -c "import json,sys;d=json.load(sys.stdin);v=d['dist-tags']['latest'];print(v,d['versions'][v]['dist']['tarball'])"
    curl -sSL -o t.tgz <tarball-url> && mkdir <包名> && tar xzf t.tgz -C <包名> --strip-components=1
GitHub 仓库（clone 被墙时）:
    curl -sSL -o drm.tgz https://codeload.github.com/<owner>/<repo>/tar.gz/refs/heads/main
    （github.com 直连超时；codeload/api.github.com 通）

## 4. 已知相关包清单（2026-10-15 扫描，11 关键词去噪音后）
| 包 | 用途 | 状态 |
|---|---|---|
| dsh-redteam-mode@0.13.1 | 自包含红队模式插件（五角色预设+SQLite 事实库+控制台）| 已解包分析: ai-assisted-security-verification-platform/dsh-plugins/ |
| dsh-redteam-model（SeaOf0, GitHub）| workflow-first 红队+kali-mcp 全家桶 | 已取源 /tmp/drm（易失，重取用上面 codeload 配方）|
| @playwright/mcp | 官方浏览器 MCP | 候用 |
| agent-browser | agent 浏览器自动化 | 候用 |
| opencode-pentest-orch | opencode 渗透组织器 | 参考 |
| @xorasecurity/cli / @sofagent/evolve | 安全 CLI / skill 优化 | 观察 |
其余命中多为 2016-2023 陈年噪音（电子书/壳包）。
