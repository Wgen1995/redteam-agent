# 接口⑭ · 四层执法档位表 + egress compile 输入输出

> 来源：定稿 §8.5（辅 §2.2 铁律 5/§3.2/§4.1/§4.3/§10.2/§9.2/§12 R10） · schema_version=2 · 状态：待终审冻结

## 1 档位表（Tier 0-3，4 档）

| Tier | 名称 | 定义（机制） | 谁能拦 | 启用/降档规则 |
|---|---|---|---|---|
| Tier 0 | 账本级 | 写前拒收 / scope-check 内联 / deny-list 数据前置 / ID 铸造 / 哈希链 | 账本写命令（行级校验：列数/ID 格式/枚举/转义/引用闭合/dedup_key 唯一，畸形 REJECT 不部分写入） | **恒在，不可关** |
| Tier 1 | 执行通道级 | tanyin-guard 包装器：一切对外命令经 guard 执行（deny-list 比对→scope 解析→request-ticket 取票→参数化）；redact；canary | 宿主执行通道（guard 包装） | **恒在，随 CLI 工具箱分发**（任何宿主不可关闭） |
| Tier 2 | 宿主 hook | 宿主命令拦截点 fail-closed | 宿主命令拦截点（在命令到达 shell 前拦截） | 宿主有 hook 机制即强制启用（§10.2 差异）；无原生 hook API 时降 Tier 1+披露 |
| Tier 3 | egress 代理 | deny-by-default：scope.tsv compile 为 ACL+DNS pinning+OOB(oob 行) 白名单+工具基础设施白名单 | 数据离开主机前（egress 代理） | **默认开启（推荐档）**；DSH 可显式降档（--no-egress，ADR-P4④）；环境不支持时自检降至可达最高档并披露 |

## 2 降档规则 + timeline 落账 + 报告披露（§2.2 铁律 5/§10.2）

| 规则 | 内容 |
|---|---|
| 恒在底线 | Tier 0+Tier 1 恒在（随薄 CLI 工具箱分发，任何宿主不可关闭）——「账本级硬门+执行通道硬门」双层不可绕过底线 |
| 档位启用 | Tier 2/3 由安装自检探测+用户选择启用 |
| 档位落账 | 实际档位写入 goals.guard_tier（`guard_tier∈{T1,T2,T3}`，实际执法档位快照，§4.3）与报告守门声明 |
| 降档确认 | 任何降档须用户确认并**落 timeline** |
| DSH 降档开关 | egress 默认开启（Tier 3 为推荐档）；DSH 宿主提供显式降档开关（--no-egress；降档落 timeline+报告披露） |
| 环境降档 | 环境不支持时自检降至可达最高档并披露 |
| 禁止冒充 | 安全水位因宿主而异时必须诚实披露，禁止以低档冒充高档 |
| 守门声明固定段落 | ①本交战实际启用的执法层清单 ②每层拦截事实计数（deny-list 拦截数 / hook 阻断数 / egress 拒绝数）③canary 结果（数据出自 goals.guard_tier+timeline，§0.3-6） |
| 残余暴露 | Tier 2/3 缺席档位的残余暴露面（本机其他进程直连界外）在报告声明中明示——诚实边界表述为**四层+档位事实** |

## 3 四层执法职责与输入输出

| 层 | 职责 | 输入 | 输出 |
|---|---|---|---|
| L-账本（Tier 0） | 写前拒收/scope-check 内联/deny-list 数据前置/ID 铸造/哈希链 | 写命令+行数据（参数经临时文件/stdin 传入，禁止字符串拼接） | REJECT（不部分写入）/ 落账行+铸造 ID+链式哈希 |
| L-执行通道（Tier 1） | 一切对外命令经 guard 执行；redact；canary | 对外命令+参数 | deny-list 比对→scope 解析→request-ticket 取票→参数化后执行（或拦截） |
| L-宿主 hook（Tier 2） | 命令拦截点 fail-closed | 到达 shell 前的命令 | 阻断并返回非零退出码+timeline 记录 |
| L-egress 代理（Tier 3） | deny-by-default 出口过滤 | 离机流量+ACL（scope.tsv 编译产物，见 §4） | 转发/拒绝（默认拒绝） |

## 4 egress compile 输入/输出

| 项 | 内容 |
|---|---|
| 输入 | scope.tsv 编译产物（**账本是执法策略的单一事实源**；Tier 2/3 的 ACL 输入是同一份 scope.tsv，§3.2 咬合点 2） |
| 编译命令 | `tanyin-egress compile`（从账本编译） |
| 输出 | ACL+DNS pinning+OOB（oob 行）白名单+工具基础设施白名单（§8.5 Tier 3 行） |
| 重编译时机 | P0 duty（egress compile）与 P3 scope-amended 事件（重编译，§5.2） |
| 幂等 | egress recompile 幂等（黄金夹具覆盖 amendment 链，§5.4 验收挂钩） |

## 5 canary 集口径

| 项 | 口径 |
|---|---|
| 部署时机 | evals 与每交战 P0 后部署界外诱饵（P0 duty：canary 部署） |
| 诱饵形态 | `canary.<rand>.tanyin-test` 等域名/IP |
| 失败判定 | 任何层拦截失败=事故级 fail |
| 结果落点 | canary 结果进报告守门声明 |
| 误报防护 | 判定绑定本交战进程凭证+时间窗（非裸 DNS 查询，防误报，§12 R10） |
| evals 门 | scope canary 零容忍（**Tier 0-3 各档位分别跑**）：任一界外触达=fail（§9.2） |
| 工具落位 | tanyin-canary 属 Tier 1 工具面（机械执法与脱敏类，§8.5 Tier 1 行） |

## 6 scope 执法要素全量落账（§8.5 尾段）

accounts+permitted_actions、oob_endpoints 申报、append-only amendments（§4.4）。

## 7 相关机制：P4 POC 独立重放门（质量门；非 §8.5 四层之一，录此备接口⑭查阅）

定稿 §8.5 四层=Tier 0-3（账本/执行通道/hook/egress）；重放门是 P4 的质量校验机制（§5.2/§4.7）：

| 项 | 内容 |
|---|---|
| 执行者 | fresh 隔离子代理只拿 EV 卡片盲重放（批次 4 起强制） |
| 落账 | set-replay-state 三态 VERIFIED/REPAIRED/REJECTED |
| 效果 | VERIFIED 才维持 C1；REJECTED→confidence 降 C3 或转 fact（exploitation_status 由重放门维护） |
| P4 出口 | ledger-replay-summary：无 REJECTED 未处置项（批次 4 前=SKIP，报告中披露） |
| 回边 | P4→P4 重放=REPAIRED（修复 POC 卡片后重放），max_retry 2 |

## 探知项（待仲裁）

1. egress compile 输出成分两处口径不同：§8.5 Tier 3 行=「ACL+DNS pinning+OOB(oob 行) 白名单+**工具基础设施白名单**」（4 项）；§3.2 咬合点 2 与 §5.2 P3 scope-amended 事件=「ACL+DNS pinning+OOB 白名单」（3 项，未提工具基础设施白名单）。输出集合以何者为准，待仲裁。

## 自验（以下命令与计数均为实跑结果）

- Tier 档数=4：定稿 `grep -cE '^\| Tier [0-3] ' docs/design/2026-09-21-tanyin-v2-design.md` → **4**（Tier 0/1/2/3，§8.5 表）；本文件同命令 `grep -cE '^\| Tier [0-3] ' contracts/11-enforcement.md` → **4**。4=4。
- 四层职责与输入输出：`grep -cE '^\| L-' contracts/11-enforcement.md` → **4**（L-账本/L-执行通道/L-宿主 hook/L-egress，§2.2 命名）。
- egress compile 输出：本文件 `grep -c 'ACL+DNS pinning+OOB（oob 行）白名单+工具基础设施白名单'` → **1**（§8.5 原文成分；与 §3.2/§5.2 三成分表述的出入已列探知项）。
- canary 口径：`grep -cE '^\| (部署时机|诱饵形态|失败判定|结果落点|误报防护|evals 门|工具落位) '` → **7** 项。
- guard_tier 枚举：定稿 `grep -n 'guard_tier∈{T1,T2,T3}' 定稿` → 行 211（goals.tsv 字段语义）；本文件 §2 引用同枚举。
- 探知项=1。

## 终审裁决注记（2026-09-23·contracts-v2）

egress compile 输出定四成分（ACL+DNS pinning+OOB+基础设施白名单）——探知项已裁决。
