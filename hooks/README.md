# hooks/ —— Tier 2 宿主 hook 模板（批次 2 T7）

| 宿主 | 挂载 | 模板 |
|---|---|---|
| DSH | 命令策略/沙箱档位 | dsh.md |
| opencode | 插件权限拦截 | opencode.md |
| codex | hook/权限机制 | codex.md |

语义（定稿 §8.5 Tier 2）：fail-closed——阻断=非零退出码+timeline `hook-block` 事件。
验证：hooks/simulate.py --goal-dir D --host h -- cmd...；canary probe --tier 2 调用本模拟器；真宿主挂载=批次 6。
