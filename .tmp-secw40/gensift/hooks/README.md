# hooks/ — Stop hook（宿主适配层）

`stop-hook.sh`（bash 宿主）与 `stop-hook.ps1`（纯 Windows pwsh 宿主，任务10 翻译件——
语义逐条对应，退出码 0=放行停止 / 2=阻止停止并继续；两版对同一账本的逼跑判定一致）：
宿主想结束回合时触发检查——GenSift 会话还有未分析的卡（checks.tsv 中
`kind != ext` 且 `state == unchecked` 的卡 > 0，与 SKILL.md 终态判定同口径）就阻止停止，
让编排器继续跑主循环；否则放行。

脚本自包含、只读账本、不改任何状态。数据行按 `$1 ~ /^CK-` 过滤：主循环会对
checks.tsv 整体重排序，表头行可能沉到文件末尾，`NR>1` 不可靠。

## 会话目录怎么找（两段兜底）

1. 环境变量 `GENSHIFT_SESSION` 指定会话目录（最准，见下方接法）
2. 未指定或无效时，扫描 `~/gensift-sessions/gensift-*`，取 `STATE` 为 `running`
   且 mtime 最新的会话

两者都找不到（非 GenSift 场景 / 会话已 done / 无账本）→ 直接 `exit 0`，不干预普通会话。

## Claude Code 接法（原生支持）

在 `~/.claude/settings.json`（用户级）或项目 `.claude/settings.json` 加 Stop hook：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/bin/bash /absolute/path/to/gensift/hooks/stop-hook.sh"
          }
        ]
      }
    ]
  }
}
```

同时跑多个审计时，用环境变量钉住会话，避免兜底扫描选错：

```json
"command": "GENSHIFT_SESSION=/absolute/path/to/gensift-session/gensift-20260824-120000 /bin/bash /absolute/path/to/gensift/hooks/stop-hook.sh"
```

**退出码语义（为什么是 exit 2 而不是 exit 1）**：Claude Code 的 Stop hook 中，
`exit 2` = 阻止停止、stderr 内容回喂给模型让它继续；其他非零退出码（含 exit 1）是
非阻塞错误，只把 stderr 展示给用户，回合照样结束——挡不住。所以脚本在剩余卡 > 0 时
同时向 stdout 和 stderr 输出 `继续：剩余 N 张卡未分析` 并 `exit 2`。
依据：Claude Code hooks 文档（code.claude.com/docs/en/hooks-guide）。

排障：

- 改完 settings.json 需重启会话或按宿主提示重载；可用 `claude --debug` 看 hook 是否触发
- 脚本无执行位要求（由 `/bin/bash` 显式执行），但仓库里已 `chmod +x`
- 个别 Claude Code 版本存在 Stop hook `exit 2` 不续跑的回归（如
  anthropics/claude-code#10412，按 hook 安装位置不同表现不同）；升级宿主或先用
  `bash stop-hook.sh; echo $?` 手工验证退出码再接入
- 预期停止被拦截时 UI 可能显示 "Stop hook error" 字样，属正常展示（见
  anthropics/claude-code#34600）

## opencode 接法（诚实标注：无原生 Stop hook）

opencode **没有原生的 Stop hook / loop / continue 配置**（权限模型只有 read/edit/bash/task/skill 等
工具级权限，agent 配置只有 `steps` 迭代上限，见 opencode.ai/docs/permissions/ 与 /docs/agents/）。
本脚本在 opencode 下**不会被自动执行**，配置了也没用。等价物是**插件系统**（v2.1 核实，
opencode.ai/docs/plugins/）：JS/TS 插件挂 `session.idle` 事件（assistant 每次收工时触发），用插件
上下文的 SDK client（`client.session.prompt`，POST /session/{id}/message）回灌续跑消息——社区打包件
npm `@dracondev/opencode-auto-continue` 即此机制；另 `permission.doom_loop: "allow"` 可放行宿主内置的
卡顿恢复提示（默认 ask 会打断）。注意：`session.idle` 属旧事件总线、opencode master 的事件 schema
已标 deprecated——以所用版本实际 schema 为准（字段名经 v2.1-b2 审查对源码核实）。

**⚠ 插件守卫必带 + 推荐顺序**：无条件回灌会在任意 idle 会话注入"继续"、GenSift 终态（STATE=done）后
无限回灌——插件必须先判「盘上存在 STATE=running 的 GenSift 会话目录」才回灌（最小守卫片段见 README
「宿主配置 → 防停」）。宿主推荐顺序：**首选 Claude Code（Stop hook 原生）＞ 次选 opencode+插件（带
守卫）＞ 兜底手动一键续**。装法与字段名同见 README 该节。

兜底两层：① SKILL.md 批轮纪律（D1）——主循环每回合连续 N 轮才收口，收口固定输出
`GENSIFT-CONTINUE: 剩余 M 卡(含 ext N)｜已 confirmed K｜会话 {S}` 一行，把该行原样发回即续跑；终态判定
（剩余卡 = 0）通过后才写 `STATE=done`，中途总结被循环纪律卡禁止。② 手工验证：
`bash hooks/stop-hook.sh; echo $?`（`2` = 还有未分析卡）；若用脚本/tmux 等外层包装驱动
`opencode run`，可在包装层调用本脚本并按退出码决定是否续跑。
