# dsh-plugin-tanyin（形态 C · v0.1 脚手架）

TanYin 账本的 DSH 原生插件：10 条核心账本命令工具化（typed tool）+ 战况读取。

## 安装（本地路径试装）

```bash
dsh plugin --profile web add /Users/wgen/redteam-agent/platform/dsh-plugin-tanyin
dsh web   # 重启 profile 生效
```

## 状态

- v0.1：service 面（ctx.tanyin.ledger）——命令白名单+超时+跨平台 spawn，范本对齐 dsh-bash-local（ESM/cordis/schemastery）
- v0.2（待接线）：agent tool 面——ToolDefinition 注册（schema 校验=把 32 律从纪律升为类型）
- v0.3（规划）：Web 战况面板（~/.tanyin/battles 心跳/五表水位/召回曲线）

## 配置

- `TANYIN_REPO` 环境变量：账本仓位置（默认 ~/redteam-agent）
- config.repo：插件配置覆盖
