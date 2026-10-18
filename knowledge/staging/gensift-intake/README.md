# GenSift — 源码自动漏洞挖掘技能

输入一个源码路径，全自动完成：攻击面枚举 → 逐卡五步证伪分析 → 盲验证 → 实时产出漏洞报告。
纯 LLM 驱动：所有分析由子代理读代码完成，确定性来自 TSV 账本 + 内联 shell 命令（零自研代码）。
覆盖不可谈判：所有 sink 必须被分析，不可跳过、不可抽样。

## 安装

技能是一个自包含目录（SKILL.md + phases/ + agents/ + classes/ + langpacks/ + fixtures/ + invariants/ + hooks/），复制即装。

**Claude Code**

```bash
cp -r gensift ~/.claude/skills/gensift        # 全局
# 或项目级：cp -r gensift <项目>/.claude/skills/gensift
```

**opencode —— 装一份即可**

opencode 原生扫描 `~/.claude/skills/`（Claude 兼容目录，见 opencode 文档 Place files 一节）。
装到上面 Claude Code 的位置即可，两宿主共用，不必再复制到 `~/.config/opencode/skills/`——
opencode 要求技能名跨所有加载位置唯一，装两份同名技能会互相冲突。
（项目级同理：`.claude/skills/` 两宿主都认。装完重启 opencode。）

### 依赖

**三平台支持矩阵（红线：macOS / Linux / Windows 原生均可跑，产物与账本格式逐字节一致——PS 侧经 dvpwa 黄金夹具 58 块双跑等价验证，见 gensift-dev/commands/golden）**

| 平台 | 命令载体 | 发起 | 说明 |
|---|---|---|---|
| macOS / Linux | bash 块（SKILL.md + phases/*.md） | SKILL.md 发起块 | 全功能；依赖下表 POSIX 工具 |
| Windows + WSL/Git Bash | bash 块（同上） | SKILL.md 发起块 | bash 可用即走 bash 分支（宿主判定见 SKILL.md 平台分支） |
| Windows 原生（无 bash，pwsh ≥7） | pwsh 节（phases/*.ps1，与 bash 块一一对应同名节） | phases/win-init.md 发起块 | 公共底座 phases/lib.ps1（含 POSIX→.NET 正则改写规则表与协议文本契约）；Stop hook 用 hooks/stop-hook.ps1；派发 prompt 模板两侧共用 phases/*.md |

宿主 × 平台四份适配件（如何驱动/如何安全终止/三重完成检测/idle 阈值校准/T2-T3 沙箱边界）：`hosts/adapter-{claude,opencode}-{posix,windows}.md`；孤儿收尸+看门狗脚本 `hosts/reaper.sh`（posix）/ `hosts/reaper.ps1`（windows，同接口同语义）。

macOS/Linux 需下表工具（基本都自带）；宿主需支持子代理派发。

| 工具 | 用途 | 说明 |
|---|---|---|
| awk、grep、sed | 枚举、账本统计（SKILL 全部命令内联） | 系统自带 |
| find、ls、cat、wc、sort、comm、mkdir、touch | 文件清单、排序对账 | 系统自带 |
| shasum | 哈希 | macOS / Git Bash 自带；Linux 无 Perl 环境常无此命令，用 sha256sum 等价替代——两者输出格式一致（`shasum -a 256` ≡ `sha256sum`，`-c` 校验互通）。SKILL.md 正在接入 `command -v` 探测回退（init 块的 HASH 变量）；若你拷贝的版本在冻结/I2 处仍直写 `shasum`，手工替换成 `sha256sum` 即可。调用点：冻结（生成 frozen.sha256）、终态 I2 校验、machine-fields 的 F-id 短哈希 |
| python3 | **不需要** | 早期版本有 1 处调用，已移除；旧拷贝若报 python3 缺失请更新技能目录 |

### Windows

- **pwsh 7 原生路径（推荐，无需 bash）**：装 PowerShell 7 后按 SKILL.md「平台分支」发起——宿主探测无 bash 时读 `phases/win-init.md`，命令块逐节取 `phases/*.ps1` 同名标题节执行（`. "$S/env.ps1"` 纪律与 bash 侧 `env.sh` 同构）；Stop hook 接 `hooks/stop-hook.ps1`
- **opencode**：默认用 PowerShell 执行命令——按上文 pwsh 原生路径走，或按 opencode 文档配置 Git Bash 作为 bash 工具的执行器后走 bash 分支
- **Claude Code**：装 Git Bash 即走 bash 分支；无 Git Bash 的机器走 pwsh 原生路径

## 使用

在宿主里说一句话：

```
使用 GenSift 审计 /绝对路径/到/源码
```

- 可选指定输出目录：`输出到 /path/to/dir`（默认 `~/gensift-sessions`）
- **可选给 advisory 清单（强烈建议——优先级立即有信号）**：目标若有已知 CVE/历史漏洞，发起时附
  `advisory=/绝对路径/cves.tsv`（每行 `CVE-ID<TAB>file:line`）：G1 锚点预检拦截跑空、种子行入候选账本、
  step1 的 cve_adj(+15) 锚点文件加权全链生效——冷启动从"纯 band 概率"变成"有召回下界"。
  无清单时 cve_adj=0 如实无信号（技能**不预置 CVE 词典**——防训练记忆污染，共识 5；给清单是用户数据不是模型记忆）
- 可选指定每轮宽度：`width=N`（缺省 4——宿主并发强可调高，超宽部分下轮自然续取，无卡丢失）
- 可选指定批轮轮数：`batch=N`（缺省 3——每回合连跑 N 轮主循环才收口一次，收口输出 `GENSIFT-CONTINUE` 续跑指令一行；防自停，见下文「防停」）
- **随时可中断**：状态全在盘上，直接关掉即可；对同一源码路径再次发起会自动断点续跑，不会从头重来
- 全程自动，不向用户提问；高危类（SQLi/XSS/反序列化等 band0）优先处理，每轮结束都刷新实时索引——不用等跑完才能看结果

## 宿主配置（全自动的前提）

两宿主的默认权限策略都会打断全自动——审计大规模跑起来之前先过本节。

**Claude Code**

先说清一个事实：GenSift 的每个命令块都以 `. "$S/env.sh"` 开头、大量块以 `for`/`while`/`{` 开头，
按命令前缀匹配的 `Bash(awk:*)` 式放行**覆盖不了这些形态**——逐条弹窗挡不住。可用的做法按侵入性排序：

1. **会话内放行 Bash**：跑起来后第一次弹窗选 "always allow"（对本会话的 bash 类命令生效），后续基本安静
2. **项目级配置**：在审计工作目录的 `.claude/settings.local.json` 放 `"permissions": {"allow": ["Bash(*)", "Read", "Write", "Edit"]}`——`Bash(*)` 是全量放行 bash，只在审计专用目录里这么配
3. `--dangerously-skip-permissions` 跳过全部询问，等于把宿主对这台机器的操作权完全交给会话——审计目标不可信时不要用

技能本身只读源码树、写会话输出目录（默认 `~/gensift-sessions`），不碰源码。写会话目录的
文件若被 Edit 权限拦截，`acceptEdits` 可省事。

**opencode**

- `external_directory` 默认 `ask`：凡工具触碰启动目录之外的路径就会询问。从别的目录启动
  opencode 去审计 `/abs/src` 会一路被打断。放行源码路径 + 会话目录 + 技能目录：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "external_directory": {
      "/绝对路径/到/源码/**": "allow",
      "~/gensift-sessions/**": "allow",
      "~/.claude/skills/gensift/**": "allow"
    }
  }
}
```

- `doom_loop` 默认 `ask`：同一工具以**完全相同的输入**重复 3 次即触发。GenSift 主循环每轮
  重复执行形态相近的状态命令，长会话可能命中；命中时选 always，或自行权衡后把 `doom_loop`
  设为 `allow`
- 最省事的绕法：**在源码根目录启动宿主、输出目录设在项目内**（`使用 GenSift 审计 . 输出到 ./gensift-out`），
  路径都在工作目录内，`external_directory` 基本不再触发

### 防停（防止提前收工）

长会话的最大敌人是宿主与模型的"回合收敛本能"（v2.1 aiohttp 实跑教训：会话尾部编排器自行总结收工）。宿主选择建议：**首选 Claude Code（Stop hook 原生）＞ 次选 opencode + 插件（必须带守卫条件）＞ 兜底手动一键续**。第 1 层两宿主都生效：

1. **批轮 + GENSIFT-CONTINUE（技能内建）**：主循环每回合连续 N 轮（缺省 3，发起指令 `batch=N` 可调，与 `width` 同法）才收口一次。收口不是总结——step6 固定输出一行
   `GENSIFT-CONTINUE: 剩余 M 卡(含 ext N)｜已 confirmed K｜会话 {会话目录}`（这是终态完成前唯一合法的回合结束形态，SKILL.md 循环纪律卡第 9 条"回合终结白名单"），把该行原样发回即续跑下一批。中途总结被纪律卡禁止（进度只落 progress_board 的 NOTICE 行与 live index）。唯一合法收口=终态完成（STATE=done）。
2. **Claude Code（首选宿主）**：原生 Stop hook——`hooks/stop-hook.sh`（配置示例见 `hooks/README.md`）：会话还有未分析卡时 `exit 2` 阻止收工并把剩余数回喂模型。
3. **opencode（次选——无原生等价物，需插件）**：2026-08 核实（opencode.ai/docs 的 permissions/agents/plugins 三页）：**无原生 Stop hook、无 loop/continue 配置项**；agent 配置只有 `steps`（迭代上限，方向相反——不设上限即"模型自己决定何时停"，这正是自停根源）。权限模型里唯一沾边的内置机制是 `permission.doom_loop`（agent 疑似卡住时宿主自动发恢复提示，默认 `ask` 会弹窗打断，设 `"allow"` 放行）。等价物是**插件系统**：JS/TS 插件挂 `session.idle` 事件（assistant 每次收工时触发），用插件上下文的 SDK client（`client.session.prompt`，POST `/session/{id}/message`）回灌一条续跑消息。注意：`session.idle` 属旧事件总线、opencode master 的事件 schema 已标 **deprecated**——以所用版本实际 schema 为准（字段名经 v2.1-b2 审查对源码核实）。装法二选一：
   - 社区打包件：npm `@dracondev/opencode-auto-continue`（opencode.json 的 `"plugin"` 数组里加一行即装，同款 session.idle+回灌机制——装前确认其守卫条件合意）
   - 自写插件放 `~/.config/opencode/plugins/`（或项目 `.opencode/plugins/`），**守卫必带**：

   > ⚠ **不要无条件回灌**：会在任意 idle 会话注入"继续"（污染非 GenSift 会话），且 GenSift 终态（STATE=done）后无限回灌烧 token。示例已带最小守卫——只在盘上存在「STATE=running 的 GenSift 会话目录」（账本在盘）时回灌，终态即停：

   ```ts
   import { existsSync, readFileSync, readdirSync, statSync } from "node:fs"
   import { homedir } from "node:os"

   export const GenSiftContinue = async ({ client }) => ({
     event: async ({ event }) => {
       if (event.type !== "session.idle") return
       let live = false                       // 守卫：有 running 态 GenSift 会话才回灌
       try {
         const root = `${homedir()}/gensift-sessions`
         for (const d of readdirSync(root)) {
           const p = `${root}/${d}`
           if (!d.startsWith("gensift-") || !statSync(p).isDirectory()) continue
           if (existsSync(`${p}/checks.tsv`) && existsSync(`${p}/STATE`)
               && !readFileSync(`${p}/STATE`, "utf8").includes("done")) { live = true; break }
         }
       } catch {}
       if (!live) return
       await client.session.prompt({ path: { id: event.properties.sessionID }, body: { prompt: "继续" } })
     },
   })
   ```

   （事件/字段名以 `@opencode-ai/plugin` 类型定义为准；输出目录非缺省 `~/gensift-sessions` 时守卫路径随之改。）
4. **兜底：手动一键续（零配置）**：收口行 `GENSIFT-CONTINUE: …` 本身就是为此设计的续跑锚点——把该行原样发回即可；用脚本/tmux 包装 `opencode run -c "继续"` 驱动也可（hooks/README.md 同结论）。

## 超时

两宿主的 bash 工具默认单次命令超时约 120s。GenSift 的攻击面枚举（逐 pattern 的 grep、
全库 find）在大库上单条命令会超 120s，被杀掉后主循环拿不到清单、卡在半路。

- **Claude Code**：单次调用带 `timeout` 参数（毫秒，上限 600000）；或设环境变量
  `BASH_MAX_TIMEOUT_MS` 抬高上限。千文件级库必须调
- **opencode**：bash 工具调用时带 `timeout` 参数（毫秒）调大
- 经验值：千文件级库把枚举类命令调到 300000–600000ms

## 首次运行检查单

装好后按序确认：

1. **技能被识别**：Claude Code 输入 `/gensift` 看是否出现补全；opencode 看 skill 列表
   （`<available_skills>`）里有没有 gensift。直接 `/gensift /绝对路径/到/源码` 调用也可以
2. **模型要求**：强长上下文模型 + 子代理派发能力。GenSift 是"编排器 + 子代理"架构，
   编排器模型弱会直接违反元规则（自己下场读代码判漏洞）
3. **成本量级**：每轮约 width+3 个子代理（缺省宽度 4 + fw/term/ext 保底各 1），每个 sink 一张卡独立分析——
   token 消耗与卡数成正比，与文件数成正比；百文件级数小时、千文件级过夜（见下节"预期"）
4. **并发**：step2 在同一条消息里并行派发多个子代理，不是串行等待——宿主需支持并行子代理；
   每轮派发宽度缺省 4（v2.1 裁决：并发不加宽，提速走批轮），发起时 `width=N` 可调
5. **上下文压缩形态**：编排器上下文里只有命令与账本摘要，不装源码正文；大库跑几十轮后宿主
   可能触发上下文压缩，但状态全在盘上（checks.tsv / STATE / 各分片），压缩不丢进度，
   重启会断点续跑

## 输出（输出目录/gensift-时间戳/）

| 文件 | 内容 |
|---|---|
| `live_findings_index.md` | **实时索引**（每轮刷新，五节）：**第 0 节审计脉搏**（闭合数/状态分布/交付面占比——test 污染持续可见/最接近 candidate 的卡/ETA+token 累计——零发现轮次也回答"在干什么、为什么没有"）/ severity 降序发现表 / open 候选表 / 近期活动（近 3 轮派发）/ NOTICE（卡顿/plateau/降级机械状态行） |
| `findings/F-*.md` | 每个发现一份**自包含**九节报告：概述/证据链(逐行原文引证)/净化分析/利用前提/PoC/定级/根因修复/同类横向/参考 |
| `report.md` | 终态汇总（机械投影；附录含不变量与 G2/G3 门原始输出留档） |
| `coverage.md` | 覆盖披露：每张卡的下场可查，"没发现"必须能解释 |
| `combinations.md` | 跨 finding 组合风险（pre-auth 链/原语组合/与已知 CVE 组合——Reporter 语义创作，阶段性刷新） |
| `joins.tsv` | 跨模块拼链账本（Egress=契约=Ingress；assumptions 非空自动生成 follow-up 卡） |
| `progress_board.md` | 每轮派卡/候选/闭合/剩余计数 + NOTICE 阈值行（慢于预估/卡顿/级联撤销） |
| `machine-fields.tsv` | 机器可读发现账本 |
| `audit/invariants.md` | 终态不变量检查结果（I1-I20 全量 + 能力边界列） |
| `audit/g2.md` | G2 闭卷对账（三向计数/每卡下场可指认/CVE 编号污染剔除） |
| `audit/stability-diff.md` | G3 双跑稳定（fingerprint join：新增/消失/变级 + 归因；单跑 N.A.） |
| `audit/desensitize-scan.md` | 脱敏扫描（session 敏感等级处置——见下节） |
| `EXIT_CODE` / `STATE` | 退出码与会话状态（见下节） |

## 退出码（CI 集成语义）

终态写入 `$S/EXIT_CODE`，`$S/STATE` 同步（`running` / `done` / `aborted-l1` / `interrupted`）：

| 码 | 语义 | 触发点 |
|---|---|---|
| 0 | 全闭合：分母与 ext 卡全部裁定，无 degraded、无 plateau、partial 占比 ≤10% | 终态块（phases/terminal.md） |
| 1 | L1 违例：分母 unchecked 回升超出 retract 豁免——技能缺陷级终止（STATE=aborted-l1） | 主循环 step0 |
| 2 | 有披露未全闭合：degraded 存在 / plateau 强制停轮 / partial 缺口 >10%（D-086）/ 终态前被中断（STATE=interrupted） | 终态块 / Stop hook |
| 3 | 门未过（v1.4.0-S14）：**0.0 pattern-lint/I1 fixture 抽样门 FAIL（坏 ERE/禁用构造/死 pattern/过宽 pattern——未验证知识禁止进枚举，B-079）**｜ G1 锚点预检 FAIL（锚点不在冻结清单内，跑前即拦）｜ I2 冻结 FAIL（清单被改过）｜ G2 闭卷 FAIL（卡下场不可指认，或 finding 叙述携带 CVE 编号=闭卷污染）｜ G3 双跑 FAIL（confirmed 指纹重合度 <0.8，或机械层分母不一致且无 refreeze 留痕） | phase0 0.0（lint 门）｜phase0 0.5（G1）｜终态块（G2/G3 门块产出 audit/g2.md、audit/stability-diff.md） |

优先级 3 > 1 > 2 > 0；CI 里 `test "$(cat EXIT_CODE)" = 0` 即全绿门。中断路径（A2 直接关宿主）：Stop hook 兜底写 `STATE=interrupted` + 退出码 2，同源码路径再次发起自动断点续跑。

## 敏感等级与战果口径

- **session 目录按"含源码级敏感数据"等级处置**：账本/分片按不变量 9 保留源码原文（secrets 明文在内）——这是"全文相等"契约的必然代价，声明而非缺陷。共享/归档 session 前先看 `audit/desensitize-scan.md`（终态自动产出，逐文件计数 ≥32 位连续字母数字串的潜在密钥命中）；非零命中时按敏感等级隔离归档，**不要手工掩码账本**（会破坏不变量 9 对账）
- **战果口径**：以确认修复率为最硬证据（finding 第 7 节的验收用例重跑通过即修复确认）；"复现已披露 CVE"因无法排除训练记忆只作辅助证据——G2 闭卷门会把 finding 叙述里出现的 CVE 编号记污染剔除，报告不靠编号说话

## 预期

- 耗时与项目规模成正比：百文件级数小时，千文件级可能过夜；token 消耗大（每个 sink 独立分析）
- 发现质量分层：confirmed（盲验证通过）优先看，unconfirmed 是待人工复核的候选
- secrets 类引文自动掩码，原文以 file:line 指针交付

## 目录结构

```
SKILL.md        编排器入口页（发起 + 循环纪律卡 + 阶段索引，≤120 行，渐进式加载的唯一常驻指令）
phases/         渐进式加载引用件（phase0 / main-loop / l2 / terminal——59 个命令块的载体，执行到哪阶段读哪件）+ win-init.md（纯 Windows 发起）+ *.ps1 ×5 + lib.ps1（58 块的 pwsh 翻译件与公共底座，块=同名节一一对应）
agents/         六角色提示词（recon/analyzer/verifier/summarizer/confirmer/reporter）
classes/        26 页类判据（24 个漏洞类 + term.md + fixture-spec.md）+ patterns/（59 个 .pattern 文件，约 509 条 ERE）
langpacks/      java/python/ts 入口枚举与 guards 五段规则
fixtures/       正/负/噪声三件套校验语料（1500+ 样本）
invariants/     业务不变式（零售域首批）
hooks/          Stop hook：会话有未分析卡时阻止宿主收工（接法与宿主差异见 hooks/README.md；bash/ps 双版本）
hosts/          宿主×平台适配件×4（如何驱动/安全终止/三重完成检测/校准/沙箱边界）+ reaper 收尸/看门狗脚本（sh/ps1）
```

## 放行门（真跑验收——v2.1-M2）

机制全绿（回放 R3-R14）不等于效果达标。每个技能版本放行前必须过**真跑放行门**：

1. **至少一个真宿主真目标的完整会话，≥10 轮**（真宿主=Claude Code 或 opencode 实驱动；真目标=真实第三方源码树，
   非合成夹具；宿主中途无人工干预续跑 ≥10 轮本身即 D1 防停验收）
2. **效果审计全绿**：对该会话目录跑 `bash gensift-dev/replays/audit-live.sh <会话目录>`（M1 效果验收层）——
   - E1 前 5 轮派单交付面占比 ≥90%（test/demo 污染被 D4-A 压住）
   - E2 优先级动态性：轮间派单构成有变化 + 证伪零 FACT 违约为 0（D4-D 反馈闭环活的）
   - E3 若有连续 3 轮零候选，live index 第 0 节必有"为何零"分析
   - 报告落 `<会话>/audit/effect-audit.md`，随会话归档；退出码 0=全绿
3. **Class A 三项抽检**（guards 五段填充质量 / Verifier 对 OBS 引文行使用 / coverage 披露信息量）是**质量数据不是放行
   阻断**——如实记录在审计报告里，趋势恶化走 CALIBRATION 通道，不静默

首轮基线：aiohttp 首跑会话（2026-08-25）经 audit-live.sh 审计 E2b FAIL（14 张证伪零 FACT）——该会话先于 D4-D
契约，FAIL 是诚实基线不是回归；放行标准以新契约下新会话为准。

## 指令面公示（两数公开，不混算）

实测（`wc -l`，2026-08-27 v2.1 批次 2 后重算——任务 11 终检口径 + 批次 1（D4/D3'/D6）+ 批次 2（D1 批轮收口/D2 审计脉搏）并入）：

| 口径 | 实测 | 预算 |
|---|---|---|
| 入口页 `SKILL.md`（发起 + 平台分支 + 循环纪律卡 + 阶段索引 + 红线 + 交付物清单） | 120 行 | ≤120 行（D-001，恰在上限） |
| 编排器指令面总量 `SKILL.md + phases/*.md`（59 个命令块，含引用件内派发模板） | 3282 行 | 另计，不占入口预算 |
| 角色提示词 `agents/*.md`（六角色） | 244 行 | 另计（各页自限：verifier ≤120） |
| 方法层 langpacks（guards 转录规则 744；sources/persisted/gadgets 结构化数据 189） | 933 行 | 见下方 D-004 口径修订 |
| 类页面 `classes/*.md`（26 页 = 24 漏洞类 + term 判据页 + fixture-spec） | 1646 行（19 页 >60 行叙事） | 见下方 D-005 口径修订 |

口径说明：

- **入口 ≤120 行**约束的是常驻上下文的入口指令量：编排器每轮只需重读入口页的循环纪律卡，命令块按阶段从 `phases/` 引用件渐进加载（执行到哪一步才读哪件），引用件内不再引用引用件（一层深度）
- **指令面总量另计**：拆分只是搬运不删减，命令一字未少——总量单独立账，与入口预算分开数、不混算
- 与 D-008「核心指令面 ≤1,200 行」对账：以 SKILL.md+phases 的**编排器指令块本体**（非叙事注释）口径逼近，任务 11 重算 59 块总量 3095 行已超原 1,200 行预算——D-008 预算口径按「入口 ≤120 硬预算 + 引用件/角色页/方法层三轴单列软公示」修订（公示即对账，非静默超支）；压缩属后续瘦身批
- **D-004 方法层 ≤450 行口径修订**：langpacks 方法件实测 933 行（guards 转录规则 744 行为知识资产本体——按「机械可读知识 vs 编排器指令」两轴拆分公示：guards/sources/persisted/gadgets 为 LLM 子代理读入的知识语料，非编排器指令面）；原 450 行预算按此口径修订并公示，压裁属后续知识资产瘦身批
- **D-005 类页面 ≤60 行叙事口径修订**：26 页实测 1646 行、19 页超 60——模式行/表格下沉 pattern 数据文件与压叙事属后续批；当前以页首来源/校准行（B-116）+ ⑫ 实际档位行（D-066）维持可对账性
- **D-037 类×语言矩阵缺口披露**：pattern 文件 59/72（6 业务类仅 java，其中 payment-logic/perm-model 为 judgment-only 空模式——判据主体在 invariants）；coverage.md 类×语言矩阵每 run 如实投影该缺口
