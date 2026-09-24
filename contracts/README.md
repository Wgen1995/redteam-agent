# 探隐契约冻结（批次 0）

> **状态**：✅ 已冻结（git tag contracts-v2 · 2026-09-23）· schema_version=2 · 来源：docs/design/2026-09-21-tanyin-v2-design.md（评审通过版+当日终审裁决）
> **冻结规则**：①只誊不创——定稿为唯一来源，契约不得新增/删减语义；②抽取中发现定稿内部矛盾→登记文末"探知项"待仲裁；③冻结（git tag contracts-v2）后任何变更走 schema_version 递增+迁移命令，禁止直接改。

## 16 项接口 ↔ 契约文件对照

| # | 接口 | 契约文件 | 定稿来源 |
|---|---|---|---|
| ① | 13 表 schema 全字段 | 01-ledger-schema.md | §4.2-§4.10 |
| ② | 10 边词汇 | 01-ledger-schema.md | §4.8 |
| ③ | 37 条账本命令签名 | 02-commands.md | §5.3+附录 A |
| ④ | {{vault:cred-N}} 占位符+vault 条目格式 | 03-credentials.md | §8.4 |
| ⑤ | phases.yaml schema+九门断言 | 04-phases.md | §5.2 |
| ⑥ | scope schema（include/exclude/oob/account-grant/amendment_of） | 05-scope.md | §4+§8.5+§5.4 |
| ⑦ | POC 四要素+EV/FD 卡片 front-matter | 06-evidence-cards.md | §4.9/§4.11 |
| ⑧ | findings 字段+FD 六字段映射 | 06-evidence-cards.md | §4.7/§4.11 |
| ⑨ | 统一提交 schema | 07-submission.md | §6.1 |
| ⑩ | manifest 模板+纪律能力声明 | 08-manifest.md | §6.3 |
| ⑪ | CLI 工具箱命令面+铁律 7 边界 | 09-cli-surface.md | §2.4 |
| ⑫ | tools.lock 格式+ECDSA 验签 | 10-toolchain-lock.md | §10.1 |
| ⑬ | creds 契约（kind 二分/material meta 位/authz-diff 语义） | 03-credentials.md | §4.10+§6.6（评审裁决已并入） |
| ⑭ | 四层执法档位表+egress compile IO | 11-enforcement.md | §8.5 |
| ⑮ | 安装矩阵布局+交战区路径约定 | 12-install-layout.md | §10.1-§10.3 |
| ⑯ | 报告模板章节骨架（中文合规六要素） | 13-report-template.md | §11 契约⑯ |

## 评审裁决已并入（2026-09-23 导读评审）

- revert_cmd 分层：外部副作用必登（无逆者 irreversible+L3）/纯账本免登（§0 决策 #4/§4.10/P6.0）
- creds：kind 二分不变+material meta 位（ntlm-hash|ssh-key|x509）→ 契约⑬
- 首批实测三宿主（DSH/opencode/codex）；walcode/CodeBuddy 装得上+披露未实测 → 契约⑮
- token 效率门首版告警、批次 6 前转硬门（验收口径，非本批契约）
## 冻结范围注记（2026-09-23 评审确认）

- 知识库契约（技法页/先例页 front-matter、graph.ndjson 格式、四门槛晋升）按定稿设计**留批次 5 冻结**——批次 1-4 不依赖，非缺失。
- 37 条账本命令逐条签名：定稿仅载命令名与分类（附录 A 缺位），签名属起草项，处理方式待终审仲裁。

## 终审裁决记录（2026-09-23·冻结时并入）

1. 命令面 37→**41**（九门断言四条并入校验类；set-cred-status 归写入：写19/查11/校验10）。
2. kind 定死四值；amendment 走 amendment_of 链。
3. egress compile 输出四成分。
4. timeline/budget 补 schema_version、matrix 补 frozen_at、creds 补 material（142→146 字段）。
5. PG 规范形 / budget scope 分工 / score 空值语义 / 四要素卡片承载 / walcode·CodeBuddy Tier 1 起步。
6. vault 条目格式与 hash-recheck 范围等推导项随 02a/03 转正（【推导】标注保留可追溯）。
7. state.md 结构留批次 3 冻结；知识库 schema 留批次 5。

## v2 勘误（2026-09-23·批次 1 施工期）

- findings + 列（CVE/CWE/GHSA  分隔，非 Nday 留空）；intents kind 枚举 +；P3 第四生成源=组件指纹→Nday 候选 intent（匹配源离线=先例页+本地 CVE 快照，联网仅 P6 核验）。字段总数 146→**147**。零存量数据期勘误，不升 schema_version。

## v2 勘误补记（2026-09-24·批次 3 施工期）

- 契约⑨（09-cli-surface.md）工具面 10→**11**：增补第 11 工具 tanyin-phases（phases.yaml 确定性状态机运算；G-1 裁决，允许类=四类允许之首「确定性账本运算」）。微版本勘误通道，不升 schema_version——详见该文件文末勘误补记。
- 契约 02a（02a-command-signatures-draft.md）§13 checkpoint 参数扩展（G-10：--timestamp/--session/--release/--round/--note/--spawn）与 state.md v2 十键行结构（G-6）回注。微版本勘误通道，不升 schema_version——详见该文件文末勘误补记（批次 3 T13 收口）。

## v2 勘误补记（2026-09-24·批次 3 评审收尾）

- 契约⑨（09-cli-surface.md）tanyin-phases 子命令枚举三处 6→**7**：补第 7 子命令 denominator-ready（分母就绪门，PROTOCOL §4；Important-1）。微版本勘误通道，不升 schema_version——详见该文件文末勘误补记。

## v2 勘误补记（2026-09-24·批次 4 施工期·T1/G-12 裁决）

- 契约①（01-ledger-schema.md）§3.6 assets.type 枚举九值→**十一值**（+cloud-storage/human-factor，细分落 meta=sub:…；§1 变更表第 6 行要点同步）。微版本勘误，不升 schema_version。
- 契约⑨（07-submission.md）§2 assets[].type 枚举串同步十一值。微版本勘误，不升 schema_version。
- 契约 02a（02a-command-signatures-draft.md）§8 add-asset 拒收条件改十一值枚举；「pivot/foothold 批次 4 前启用=REJECT」分支退役（§4.8 兑现）。微版本勘误，不升 schema_version。
- phases/PROTOCOL.md §4 类映射补 cloud-storage→A5、human-factor→A7 两行（G 台账 G-12 清账，原「A5/A7 无对应值」注记作废）。

## v2 勘误补记（2026-09-24·批次 4 施工期·T2/G-2 裁决）

- 契约 02a（02a-command-signatures-draft.md）§12 matrix-set 拒收条件勘误：submatrix: 四条件放行新键行铸造（原子铸造新表面×VOCAB 全集行，timeline 事件 submatrix-mint）+reason 前缀规则修正（旧前缀空→任意前缀首次归类放行；旧前缀非空且≠新→REJECT——修 authz-diff 首次落格潜伏阻塞）。微版本勘误，不升 schema_version。
