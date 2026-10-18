# capability_gate 预检快照 · 2026-10-20（实测）

> 命令：`python3 scripts/capability_gate.py`（对 HEAD 增量对比；rc 0=过/1=拒合并/2=环境）。本档=首仗筹备预检快照，**只记录不修**（缺口报母舰裁）。

## 一、实测结果

| 检查 | 命令 | 结果 |
|---|---|---|
| 棘轮门 | `python3 scripts/capability_gate.py` | **rc=0 verdict=pass**（changed=false：prompt_files/technique_cards/tool_lock 三面零变更 vs HEAD，delta=null） |
| GT 注册表完整性 | `python3 evals/gt/gt_verify.py` | **rows=27 pass=27 fail=0 chain-steps=12**（锚根=evals/gt/snapshots/zl-repo），rc=0 |
| 棘轮基线档案 | `ls ~/.tanyin/capability-baseline.json` | ❌ **不存在**（见缺口1） |

## 二、缺口清单（如实记录，不修）

1. **棘轮持久锚从未落盘**：`~/.tanyin/capability-baseline.json` 不存在——`--update-baseline` 从未跑过。现状每次 gate 都是对 git HEAD 的增量对比（能力面文件变了才出 delta），「只升不降」缺少**跨提交的分数基线锚**。点火影响：不阻塞点火（gate 本身 rc=0），但首仗后的「能力曲线落点」（first-battle-checklist:19 战后必做）没有既有锚可挂。
   - 待母舰裁：是否在点火前跑一次 `python3 scripts/capability_gate.py --update-baseline` 铸基线锚（跑=写入仓外 ~/.tanyin/，非引擎改动，但属「动状态」故不顺手做）。
2. **ZhuLong 战场无 session 判分卷**：gt-index.tsv 里 zl-* 三件是 source-gt/chain-gt 口径，黑盒会话判分仍用 range-56-v5 的 scorer+GT 形——代卷步骤见 gt-exam-readiness.md（本舰已备说明，产卷动作留点火面）。

## 三、结论

capability_gate 现状 **rc=0 可过**（零能力面变更=零回归风险暴露），GT 注册表 27/27 完整；唯一结构性缺口=基线档案缺位（缺口1）+ZhuLong 代卷待产（缺口2，说明已就位）。
