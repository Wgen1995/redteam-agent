# redteam-agent（暂名）

一人红队 AI 自动化渗透测试 skill/agent。调研与设计阶段。

- 运行时：DSH / opencode / codex（agentskills.io SKILL.md 规范）
- 输入：授权范围 + Web 凭据 + 后台 IP（黑盒为主，偶有安装包/源码）
- 输出：POC+EXP 卡片 / findings.jsonl / 中文报告 / 证据目录
- 平台：macOS/Linux 原生；Windows 用 `py -3` 等价入口（UTF-8/LF 已强制，见 cli/README.md「Windows 用法」；CI 双平台矩阵 .github/workflows/ci.yml）
