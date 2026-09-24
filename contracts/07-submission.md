# 07 统一提交契约（submission.json，接口⑨）

> 来源：定稿 §6.1（辅引 §2.1/§3.4/§4.1/§4.6-§4.10/§5.2/§5.3/§6.3/§9.1/§11，随行标注）· schema_version=2 · 状态：待终审冻结

本文件为批次 0 接口⑨（统一提交 schema，§6.1）的誊录件（定稿 §11 批次 0 行）。只誊不创：全部语义来自定稿；各数组子字段的枚举约束以「对应账本同名字段（辅引 §4.x）」标注——§6.1 仅载字段名，枚举语义誊自账本侧对应列。

## 0 定位与数据形状（§6.1 契约双轴）

每引擎三样：

| # | 样 | 内容（§6.1 原文） |
|---|---|---|
| ① | manifest | 引擎自述（契约⑩，见 contracts/08-manifest.md） |
| ② | 输入 | session 目录＋目标描述＋已有 facts 摘要（跨引擎知识流动入口） |
| ③ | 输出 | 统一提交文件→`submissions/<intent-id>/`，总控验收后落账，**引擎不直接写账本** |

## 1 提交目录布局（§3.4）

`submissions/<intent-id>/`＝submission.json＋artifacts/＋operations.log；artifacts 运行时以 `submissions/<intent-id>/artifacts/` 为准（§3.4 规则）。

## 2 submission.json 全字段（§6.1 定稿）

顶层 9 字段：

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| intent_id | 文本 | 如 INT-g1-0007；ID 铸造＝ledger-next-id 原子分配，子代理/引擎无铸造权（§4.1）——本字段为委派 intent 的引用回显 | intent 标识 |
| engine | 文本 | 引擎名（定稿示例：web-blackbox） | 产出引擎 |
| status | 枚举 | ∈{done, no-findings, failed, blocked, partial}（5 值） | 提交状态 |
| facts | 数组 | 元素 4 字段（下表） | 事实清单 |
| findings | 数组 | 元素 12 字段（下表） | 发现清单（引擎提议，见 §3） |
| assets | 数组 | 元素 3 字段（下表） | 资产清单 |
| edges | 数组 | 元素 4 字段（下表） | 边清单 |
| creds | 数组 | 元素 6 字段（下表） | 凭据清单 |
| operations_log | 文本 | ＝"operations.log" | 操作日志文件名 |

数组子字段（枚举为辅引：对应账本同名字段 §4.6-§4.10）：

| 数组 | 字段 | 枚举/约束（辅引出处） | 说明 |
|---|---|---|---|
| facts[] | kind | ∈{port,service,http,info,vuln-clue,authz}（§4.6） | 事实类型 |
| facts[] | target | — | 目标 |
| facts[] | detail | 落账即脱敏（§4.6） | 细节 |
| facts[] | confidence | 0-1（§4.6） | 置信度 |
| findings[] | title | — | 标题 |
| findings[] | confidence | 四级（C1/C2/C3/➖🛑）（§4.7） | 两维评级之一 |
| findings[] | impact | ∈{高,中,低}（§4.7） | 两维评级之二 |
| findings[] | exploitation_status | ∈{verified,suspected,ruled_out}（§4.7） | 利用状态 |
| findings[] | auth_context | 空（未认证）或 `CRED-{id}`（§4.7） | 认证上下文 |
| findings[] | reproducible_steps | ≥1 强制（§4.7） | 可复现步骤 |
| findings[] | evidence_refs | — | 证据引用 |
| findings[] | location | — | 位置 |
| findings[] | dedup_key_proposed | 引擎只提议（§6.1，见 §3） | 去重键提议 |
| findings[] | network_position | ∈{internet,intranet,same-host,jumphost:`<name>`}（§4.9） | POC 四要素之一 |
| findings[] | preconditions | — | 前置条件（POC 四要素之二，§4.11） |
| findings[] | expected_matcher | — | 预期匹配（对应 EV 卡片 expected，POC 四要素之四，§4.11） |
| assets[] | type | ∈{root-domain,subdomain,ip,service,app,endpoint,source-code,pivot,foothold,cloud-storage,human-factor}（§4.8+G-12 勘误） | 资产类型 |
| assets[] | value | — | 资产值 |
| assets[] | meta | — | 元数据 |
| edges[] | kind | 10 边词汇（§4.8） | 边类型 |
| edges[] | source_ref | — | 源引用 |
| edges[] | target_ref | — | 目标引用 |
| edges[] | provenance | 来源（intent/引擎/人工）（§4.8） | 出处 |
| creds[] | kind | ∈{static-cred,session}（§4.10） | 凭据类型 |
| creds[] | role | 业务角色标签（§4.10） | 角色 |
| creds[] | username_ref | 账号名或脱敏代号（§4.10） | 账号引用 |
| creds[] | secret_placeholder | 占位符（对应账本 secret_ref=`{{vault:cred-N}}`，§4.10） | 秘密占位符 |
| creds[] | obtained_via | 获取来源（对应账本 obtained_via_intent，§4.10） | 获取来源 |
| creds[] | permitted_actions | 对照 account-grant（§4.10） | 允许动作 |

## 3 提议与铸造（§6.1）

引擎只**提议** dedup_key 与 ID 引用，总控命令重算与铸造（LLM/引擎不判重不铸号）。dedup_key＝资产＋技法类（命令机械计算，重复键 REJECT——LLM 只提议不判重，§4.5）。

## 4 submission-ok 判定规则

- 总控四件事之一＝验收格式；产出必须经账本命令落盘（§2.1 铁律 1：禁止自己判漏洞、写 finding 叙述、写脚本替代账本命令）。
- 引擎级夹具判据（§9.1）：提交文件与 submission-ok 结构一致——**字段全／凭据占位符化／证据双哈希／pair_group 标注**（4 项）。
- 验收后落账＝写命令，写前拒收：列数/ID 格式/枚举/转义/引用闭合/dedup_key 唯一，畸形 REJECT 不部分写入（§4.1）。
- 单写者：所有写操作由总控串行执行；子代理/引擎只产 `submissions/<intent-id>/submission.json`（§4.1）。
- 判定不通过的处置（§6.3 失败语义五类）：

| 失败类 | 处置（§6.3 原文语义） |
|---|---|
| 格式漂移 | 首次打回加载 submission-reject.md 纠错重写一次 |
| 上下文耗尽 | partial 提交（已完成项＋未完成清单），总控拆分 intent |
| 超时 | 同 partial |
| 环境受阻 | 记 fact 附因不阻塞，intent 转 blocked（不可自动复活） |
| 工具失败 | 重试 1 次（指数退避）后换技法页备选路径或 blocked |

## 5 幂等与重入（§5.2 补充语义/§11 批次 3）

- 工件即缓存幂等续跑＝**intent done 且 `submissions/<intent-id>/submission.json` 存在→重入跳过**（§5.2 补充语义；§11 批次 3 同口径：「工件即缓存幂等续跑（intent done 且 submission.json 存在→重入跳过）」）。
- 区分：账本命令幂等为 §5.3 通用纪律（「命令幂等」）；本节幂等为 intent 级重入跳过。

## 探知项（待仲裁）

无（未发现定稿内部两处说法冲突）。

## 自验

命令实跑证据（D＝定稿路径，本文件＝contracts/07-submission.md）：

- 顶层字段：`sed -n '497,508p' $D | grep -oE '"[a-z_]+":' | sort -u | wc -l` → **9**（intent_id/engine/status/facts/findings/assets/edges/creds/operations_log）；本文件 §2 顶层表 `awk '/^\| intent_id/,/^\| operations_log/' 本文件 | grep -c '^| '` → **9**。
- findings 子字段：`sed -n '501,503p' $D | grep -oE '"[a-z_]+"' | wc -l` → 13（含数组键 "findings" 本身）→ **12**＝本文件 §2 findings[] 行数。
- creds 子字段：L506 同法 → 7−1＝**6**；facts[]＝L500 5−1＝**4**；assets[]＝L504 4−1＝**3**；edges[]＝L505 5−1＝**4**。
- status 枚举＝**5**（done/no-findings/failed/blocked/partial，L499 实跑命中整串 1 行）。
- submission-ok 判据＝**4** 项（字段全/凭据占位符化/证据双哈希/pair_group 标注，§9.1）；失败处置五类＝**5** 行（§4 表）。
- 幂等：`grep -n 'intent done 且' $D` → **2** 处（L450 §5.2 补充语义、L706 §11 批次 3），口径同一（intent done 且 submission.json 存在→重入跳过）。
- 探知项＝**0**。

## v2 勘误补记（2026-09-24·批次 4 施工期·G-12 裁决）

§2 数组子字段表 assets[].type 枚举同步为十一值：+cloud-storage/human-factor（细分落 assets[].meta=sub:…），pivot/foothold 批次 4 起启用——与契约 01 §3.6 同批微版本勘误（零存量数据期，schema_version 不递增），索引见 contracts/README.md。
