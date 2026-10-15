# 实验登记处 · 度量纪真律（v0.9d）

> 计划：docs/superpowers/plans/2026-10-14-exp-registry.md（R1）。
> 缘起：v0.9c 诚实披露——N=5 判决 b=8 c=17 的子集清单未入库，页面不可机械复现。

## 格式律

- 一个实验一个文件：`experiments/<exp-id>.tsv`，UTF-8 行式 `field<TAB>value`（可 grep）。
- 11 个登记字段（度量页缺字段降级为空串）：
  - `id` —— 实验标识（=文件名主部）
  - `question` —— 实验问题（一句可判决的话）
  - `battles_control` / `battles_treatment` —— 两臂战例清单（空格分 battle-id）
  - `gt_gen` —— GT 代（gen）口径说明
  - `decision_rule` —— 预登记判决规则（统计量+阈值，判前定死）
  - `registered` —— 登记时间（先落 tsv 再开战）
  - `status` —— 状态（进行中/已判决…）
  - `verdict` —— 判决结果（判后回填）
  - `source` —— 出处（文件:行 或机械复现口径）
  - `note` —— 备注（含不可复现情况的诚实说明）
- **预登记律：开战前必须先落 tsv（`registered`=登记时间）——无登记=度量页不认。**
- **回填律：判决后回填 `status`/`verdict`；`source` 记出处；不可机械复现的判决
  必须在 `note` 里说明验证口径与结果，不许含糊。**

## 投影（只读）

`cli/webui/metrics.py experiments_view(repo_root)` 读取本目录 →
`/api/metrics.json` 的 `experiments` 键与度量页「预登记实验」小节同源。
登记处与投影均零写入。

## 在册实验

- `directive-n5.tsv` —— N=5 双臂指令策略判决（判后回填；verdict=子集不可复原，
  见 tsv 内 note 的机械验证账）。
