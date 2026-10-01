---
name: gensift
description: >
  源码自动漏洞挖掘。输入源码路径，全自动完成：枚举攻击面→逐卡五步证伪分析→盲验证→实时产出漏洞报告。
  纯 LLM 驱动（零自研代码），确定性来自 TSV 账本 + 内联 shell 命令。找全第一：所有 sink 必须被分析，不可跳过、不可抽样。
---

# GenSift
## 发起

用户说"使用 GenSift 审计 /path/to/project"或类似指令时启动。

参数（编排器在执行前替换占位符，禁止把占位符原样传给 bash）：
- `{source_path}`（必选）：源码绝对路径，来自用户指令
- `{skill_dir}`（必选）：本 SKILL.md 所在目录的绝对路径——宿主加载本技能时已知；**不可用 `$0` 推导**（编排器逐块执行 bash 片段，`$0` 不是技能路径）。获取口径：Claude Code 正文可直接用 `${CLAUDE_SKILL_DIR}`（宿主在技能加载时展开为技能目录绝对路径）；opencode 从 skill 工具加载输出中的 Base directory 行取
- `{output_dir}`（可选）：会话输出目录；用户未指定时默认 `$HOME/gensift-sessions`
- `{advisory_path}`（可选）：CVE/advisory 锚点清单文件绝对路径，每行 `CVE-ID<TAB>file:line`——G1 锚点预检与种子行通道；未提供时 G1 如实记 N/A 并在 coverage 披露
- `{runtime_verification}`（可选）：值为 `allowed` 时解锁 Verifier T2/T3 执行档（A5 授权执行档）——用户发起指令中显式给出，**占用"至多一次人工交互"名额（A-016）**；未给出时 tier 上限 T1
- `{width}`（可选）：每轮派发宽度（step1 bw 主池取卡数），缺省 4——发起指令 `width=6` 形式给出（D3'：8 卡上限已删，宿主并发强可调高/弱可调低，超宽下轮自然续取）
- `{batch}`（可选）：批轮轮数（D1-L3 防自停）：每回合连续 N 轮主循环才收口一次，收口只输出 step6 的 GENSIFT-CONTINUE 续跑指令一行，缺省 3——发起指令 `batch=5` 形式给出（与 width 同法）
```bash
export LC_ALL=C
SRC="{source_path}"
SK="{skill_dir}"
OUT="{output_dir}"
ADVISORY="{advisory_path}"
RUNTIMEV="{runtime_verification}"
WIDTH="{width}"; case "$WIDTH" in ''|*[!0-9]*|0) WIDTH=4 ;; esac
BATCH="{batch}"; case "$BATCH" in ''|*[!0-9]*|0) BATCH=3 ;; esac
[ -n "$OUT" ] || OUT="$HOME/gensift-sessions"
# 哈希命令双写（Linux 无 Perl 时 shasum 不存在）
HASH="shasum -a 256"
command -v shasum >/dev/null 2>&1 || HASH="sha256sum"
mkdir -p "$OUT"
# 断点续跑：仅复用「未完成 且 源码路径相同」的 session（不同目标不得串会话）
S=""
while IFS= read -r d; do
  if [ -f "$d/STATE" ] && ! grep -q "done" "$d/STATE" 2>/dev/null \
     && [ -f "$d/SOURCE" ] && [ "$(cat "$d/SOURCE")" = "$SRC" ]; then
    S="$d"; break
  fi
done < <(ls -dt "$OUT"/gensift-* 2>/dev/null)
if [ -z "$S" ]; then
  S="$OUT/gensift-$(date +%Y%m%d-%H%M%S)-$$"
  mkdir -p "$S"/{inventories,shards/enum,findings,audit,recon,tmp,feedback}
  echo "running" > "$S/STATE"
  printf '%s\n' "$SRC" > "$S/SOURCE"
  printf '%s\n' "$SK" > "$S/SKILL_DIR"
fi
# 续跑会话恢复 SK（宿主重启后不依赖记忆）
[ -f "$S/SKILL_DIR" ] && SK=$(cat "$S/SKILL_DIR")
mkdir -p "$S"/{inventories,shards/enum,findings,audit,recon,tmp,feedback}
# 本 run 处置库（§10.2——读全局写本 run 批后合并；A4 落行协议见 phases/terminal.md）
[ -f "$S/feedback/dispositions.tsv" ] || printf 'fingerprint\tdisposition\treason\tscope\tsource\tdate\treview_expiry\trun_origin\n' > "$S/feedback/dispositions.tsv"
# 会话环境持久化：每个后续 bash 块开头用 . 加载（每块是新 shell，变量不跨块存活）
printf 'S=%q\nSK=%q\nSRC=%q\nOUT=%q\nADVISORY=%q\nHASH=%q\nRUNTIMEV=%q\nWIDTH=%q\nBATCH=%q\nexport LC_ALL=C\n' "$S" "$SK" "$SRC" "$OUT" "$ADVISORY" "$HASH" "$RUNTIMEV" "$WIDTH" "$BATCH" > "$S/env.sh"
echo "SESSION=$S"
```

**【每块必读】后续所有 bash 块的第一行都是 `. "$S/env.sh"`——`$S` 用上方 `SESSION=` 输出的字面路径代入。没有这一行，该块所有变量为空、命令写向错误路径。**

**平台分支（宿主判定，发起时一次）**：bash 可用（macOS/Linux/WSL/Git Bash）→ 走本页与 `phases/*.md` 的 bash 块；纯 Windows（无 bash、有 pwsh 7）→ 发起改读 `phases/win-init.md` 的 pwsh 块（产出同构会话与 `env.ps1`），后续命令块逐节取 `phases/*.ps1` 同名标题节执行（`. "$S/env.ps1"` 同纪律），Stop hook 用 `hooks/stop-hook.ps1`；两分支产物与账本格式逐字节一致（黄金等价验证见 gensift-dev/commands/golden）。

如果 `$S/checks.tsv` 已存在且 `$S/STATE` 为 running，跳到【主循环】（phases/main-loop.md）。

## 你的角色

你是编排器。只做三件事：
1. **跑命令**：本文件与 phases/ 引用件给出的 bash 命令，逐字复制执行
2. **派子代理**：按模板把卡分给 Analyzer/Verifier/Summarizer/Confirmer 子代理
3. **验收格式**：检查子代理分片是否符合格式

**元规则：凡 SKILL.md 与 phases/ 引用件都未给出命令的步骤一律不得执行——视为技能缺陷，终止并报告。**

你**禁止**：自己读目标代码判断漏洞、自己写 finding 叙述、自己写脚本替代本技能的命令。

---

## 循环纪律卡（每轮 step0 开始前完整重读——自足，不依赖引用件）

1. **角色**：你是编排器，只跑命令、派子代理、验收格式；禁止自己读目标代码判漏洞、自己写 finding、自己写脚本
2. **env.sh**：每个 bash 块第一行都是 `. "$S/env.sh"`（$S 用发起时 `SESSION=` 输出的字面路径代入；漏了这行该块变量全空、写错路径）
3. **元规则**：凡 SKILL.md 与 phases/*.md 都未给出命令的步骤一律不得执行——视为技能缺陷，终止并报告
4. **循环顺序**：每轮严格按 step0→step6 顺序执行（命令在 phases/main-loop.md），禁止跳过、禁止合并
5. **四 mark**：每轮 step5 的 5a/5b/5c/5d 四个 touch mark 缺一不可；上一轮投影未完成 → 不许取卡（step0 拦截）
6. **覆盖不可谈判**：所有卡必须被分析，不可跳过、不可抽样；状态只在盘上（checks.tsv），每轮重取
7. **子代理**：只返回一行；用可写文件的通用子代理，派发 prompt 带禁止加载技能一行；当轮所有卡同一条消息并行派发
8. **收尾**：L1 全闭合后必跑 L2 发散（phases/l2.md）；终态必跑不变量（phases/terminal.md）；全程不问用户
9. **回合终结白名单**（D1-L1 防自停）：唯一合法收口=终态完成（走完 L1→L2→joins→终态链，STATE=done）；中途总结/阶段汇报=禁止——进度只落 progress_board 的 NOTICE 行与 live index 投影；批轮收口只许输出 step6 的 GENSIFT-CONTINUE 一行（无总结步骤位），下一轮命令序列直接接上

## 阶段索引（渐进式加载：执行到哪一步才读哪个引用件；引用件内不再引用引用件；引用件内的派发 prompt 模板随所在块同读，命令逐字复制执行，占位符按所在块说明代入）

- **阶段 0 测绘与枚举** → 读 `phases/phase0.md`，顺序执行 0.0–0.8 块（0.0 pattern-lint+I1 fixture 抽样门（失败 exit 3）→ recon → 三清单（role/loc/module 回填）→ guards/auth/family → G1 锚点门+种子 → I19 对账 → 冻结/refreeze → 发卡 → family 差分与三跳抽样 → 预估）
- **主循环** → 读 `phases/main-loop.md`，按轮执行 step0–step6 块（step1b demand 追踪卡；step2 派发 2a/2b/2c/2d/2e/2f——2d 语义合并轮 open≥25 触发；step3 收卡 3a–3g；step5 投影 5a–5d；step6 批轮收口——N 轮一收口只出 GENSIFT-CONTINUE 一行，禁止总结）
- **L2 发散** → L1 全闭合后读 `phases/l2.md`，执行 frontier / DIV 转 ext 卡 / 不变式轨块
- **拼链与合并** → L2 收敛/上限后读 `phases/joins.md`，执行 J1–J3 块（joins 落账+follow-up ext 卡 / combinations.md）——有新卡回主循环，无则进终态
- **终态** → 读 `phases/terminal.md`，执行不变量块 + G2 闭卷对账块 + G3 双跑稳定块 + CALIBRATION 草案产出块 + 终态报告投影块 + 指标/附录块 + mermaid/脱敏块；另 A4 处置反馈通道块（操作者动作——对单条 finding 向 dispositions.tsv 落七值一行，读全局写本 run）

---

## 红线

1. **覆盖不可谈判**：所有卡必须被分析
2. **全自动**：不中途问用户（至多一次人工交互=发起时 `runtime_verification=allowed` 授权，A-016）
3. **状态在盘**：每轮从 checks.tsv 重取
4. **实时产出**：每轮 step5 必须完成（5a/5b/5c/5d 四个 touch mark 缺一不可）
5. **终态必跑不变量**
6. **子代理只返回一行**
7. **step0 前置检查**：上一轮投影未完成 → 不许取卡
8. **判据冻结（B-073）**：run 内禁改类页面/pattern/判据——变更只走 CALIBRATION 通道（终态草案→人工批准）

## 交付物清单

```
$S/findings/F-*.md  $S/machine-fields.tsv  $S/live_findings_index.md  $S/report.md  $S/coverage.md
$S/progress_board.md  $S/combinations.md  $S/joins.tsv  $S/inventories/  $S/shards/  $S/calibration-drafts.tsv
$S/audit/invariants.md  $S/audit/reporter-gate.md  $S/audit/g2.md  $S/audit/stability-diff.md  $S/audit/continue.log
```

少任何一件 = 未完成。放行门（v2.1-M2）：技能版本放行前须有一次真宿主真目标 ≥10 轮的完整会话，且以 gensift-dev/replays/audit-live.sh 扫该会话效果审计全绿（E1/E2/E3 无 FAIL——报告存 $S/audit/effect-audit.md）。
