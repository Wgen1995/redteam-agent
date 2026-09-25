# 契约 14 · 知识库 schema（批次 5 冻结；微版本勘误通道同契约 01-13）

> 来源：定稿 §3.4 布局+§7.1 知识系统飞轮+§7.2 初始语料入库+§9.4 双知识库抽查（辅 docs/design/2026-09-24-completeness-recon-knowledge-evolution.md K1-K8 全集）· format_version=kn-v1 · 状态：批次 5 冻结
> 载体：仓库 `knowledge/`=种子库（批次 6 安装器拷贝至 $TANYIN_HOME/knowledge/）；CLI 一律 `--knowledge-dir` 参数化；种子库只读纪律（R7）——指向仓库 knowledge/ 时一切写子命令 REJECT。

## 1 布局与版本

- 根目录：format_version（当前 kn-v1；单行文件，不匹配=拒绝操作并提示迁移）/index.md/log.md/overview.md/checklists/
  methodology/ concepts/ precedents/ entities/ targets/ patterns/{core,learned}/
  business/ retros/ cve/ sources/ staging/ client-map.example.tsv graph.ndjson
- K1-K8 类目映射：K1=methodology/（+shared/VOCAB.md）；K2=precedents/+entities/；
  K3=cve/；K4=shared/DENYLIST.md（库外既有数据文件，index.md 登记指针）；
  K5=concepts/；K6=patterns/；K7=business/；K8=retros/。
- 词表版本化：每页 front-matter 必填 vocab_version；合法值集合=shared/VOCAB.md
  的 version 行（当前 WSTG-v4.2）；lint 朗读该行取支持集。
- CLIENT-NN：client 字段一律 ^CLIENT-\d{2,}$；映射表 client-map.tsv 运行时文件
  （真值永不进仓，.gitignore 排除；example 模板进仓）。

## 2 页 front-matter schema（六类；「必」=必填；枚举值列举穷尽）

### 技法页（concepts/CP-*.md）——K5

| 字段 | 必 | 约束 |
|---|---|---|
| id | 必 | ^CP-\d{4}$ |
| kind | 必 | =technique |
| class | 必 | =K5 |
| title | 必 | ≤60 字 |
| vocab_version | 必 | ∈支持集 |
| vuln_class | 必 | 词表键或子类键（细类=wstg-XX:subclass 形）；多值 ; 分隔 |
| applicability | 必 | 适用条件一句话 |
| tool_params | 否 | 工具与参数（BurpPOC/nuclei 映射） |
| cost_hint | 必 | ∈{1,2,3}（请求量级 1=个位/2=十位/3=百位） |
| failure_modes | 否 | 失败模式与转向 |
| judgment | 否 | 判定标准（errorCode 语义分析等） |
| cve_refs | 否 | CVE 编号 ; 分隔；非空则 cve_verified 须逐个覆盖 |
| cve_verified | 条件必 | 列表 [{cve, source∈{NVD,PSIRT,KEV,vendor}, verified_at}] |
| last_verified | 必 | ISO 日期 |
| status | 必 | ∈{core, learned, demoted}（concepts 落 core/learned 皆可） |
| source_id | 必 | ^KP-\d{4}$（SOURCES.tsv 引用闭合） |

### 先例页（precedents/PR-*.md）——K2，三元组页

| 字段 | 必 | 约束 |
|---|---|---|
| id | 必 | ^PR-\d{4}$ |
| kind | 必 | =precedent；class=K2 |
| client | 必 | ^CLIENT-\d{2,}$（三元组字段①） |
| scope_asset | 必 | 脱敏指纹（占位符化域名/组件描述）（三元组字段②） |
| window | 必 | YYYY-MM-DD..YYYY-MM-DD（授权窗口，过期失效）（三元组字段③） |
| triples | 必 | 列表 [主语,谓语,宾语]×N（graph.ndjson 导出行源） |
| outcome | 必 | 结果一句话（finding 计数等） |
| applied_patterns | 否 | PT-id 列表（四门槛①复现计数载体） |
| retro_link | 否 | ^RT-\d{4}$ |
| cost_hint/last_verified/status/source_id | 必 | 同技法页 |

### 实体页（entities/EN-*.md）——K2

字段集：id/kind=entity/entity 名（如 favicon-hash:ab12cd）/aliases;分隔/occurrences 整数/pattern_stats 文本/vocab_version/status/last_verified

### 复盘页（retros/RT-*.md）——K8

字段集：id/kind=retro/client/window + 必答三问 missed（漏了什么）/trigger_gap（触发器缺哪）/weak_channel（通道弱哪）/writeback（回写到哪类）+ last_verified/status

### 模式页（patterns/PT-*.md）——K6

字段集：id/kind=pattern/use∈{ok-sample,false-positive}/vuln_class/sample_brief + 四门槛晋升字段 status∈{learned,core,demoted}

### 业务页（business/BZ-*.md）——K7

字段集：id/kind=business/industry（零售/金融…）/checklist_brief/last_verified/status

## 3 graph.ndjson 行 schema（逐行 NDJSON；export 确定性重建）

```
{"id":"<页id>:t<序号>","subject":"...","predicate":"...","object":"...",
 "source":"PR-0012","class":"K2","created":"<commit 时间戳>"}
```

- 行序=（source 页 id, t 序号）字典序；行级可合并预留（多 session 锁协议=R6 残余，维持登记）。

## 4 staging 状态机与入库流水线

```
staged →(lint 全过)→ lint-passed →(approve 人审)→ approved →(commit)→ formal
任意态 →(reject)→ rejected（终态留档 staging/）
```

- 载体：staging/staging.tsv 十列（staging_id/page_id/class/title/source_id/status/
  checksum/created/approved_by/approved_at）；log.md 追加叙述（ts|event|id|detail）。
- 机器检查（lint，tanyin-knowledge）：front-matter schema 校验/脱敏哨兵（special.py
  泄漏形态单源）/dedup_key（sha256(kind+vuln_class+标题归一)）查重/词表版本/CVE
  核验标记完备。人工审=checklists/review-checklist.md（四门槛之外的质量判断）。
- 四门槛（learned→core 晋升，全部机械可检）：①复现≥2（被 ≥2 先例页 applied_patterns
  引用）②跨目标有效（引用页 client 去重 ≥2）③人工审批（log.md approve 且
  for=promote）④无指纹泄漏（redact 哨兵零命中）。

## 5 语源登记与许可纪律

SOURCES.tsv：source_id/origin∈{cnpen,vulnclaw,bughunter,threatswarm,cep,internal}/
path/sha256/license/note/registered_at。外部语料一律 MIT 核验（LICENSE 文件在场，
VulnClaw=Copyright (c) 2026 UncleC，MIT；BugHunter/Threatswarm/CEP 执行期逐一核验）
——防投毒对称性：外部与自有语料同走一道 staging 审批门（§7.2）。

## 6 ID 前缀表（知识库自有命名空间，不与账本 §4.1 前缀混用；tanyin-knowledge 内部机械分配）

KP 语源 / STG 暂存 / CP 技法 / PR 先例 / EN 实体 / TG 目标 / PT 模式 / RT 复盘 / BZ 业务
——四位零填充字典序=时间序（账本同精神；不经 ledger-next-id）。
