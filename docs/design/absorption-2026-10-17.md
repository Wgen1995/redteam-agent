# 机制吸收 → 探隐自建设计决策（2026-10-17）
定位: 五家研究的目的=拆齿轮吸收构造思路,反哺探隐自己的设计;效果测试只是校准吸收优先级。依据: engine-parts/corpus-audit×2/vulnclaw-live-trial v2/multica-source-study+全部walks。

## 一 · 齿轮清单（吸收什么,装到哪）
### ARTEX（常驻引擎的工程技法）
| 齿轮 | 它怎么做 | 装进探隐哪里 |
|---|---|---|
| 唤醒模型 | 事件通知+心跳≥600s+防抖+六道门(engine.go:800) | v1.0b planner 常驻循环的唤醒设计 |
| 单写者技法 | planner 唯一意图源+frontier 单表 CAS 抢占 | 单写者律的无锁实现 |
| 分层记忆 | 全局资产图+任务探索图+冷节点 digest 压缩 | 账本图谱「单图两域」(E6 F1 判决同向) |
| 发现纪律 | report_finding 须真触发+可复现;retester 专职复测 | 复测域加「固定岗+自动重放」 |
| 收尾保写回 | 预算命中走 settlement 仍写回 | 地基批 O(1) 追加+收尾协议 |
| 模型韧性 | llmpool 多 profile 故障转移链 | llmpool 接线四件参照 |
### CSAI（工具面与治理）
| 齿轮 | 装进探隐哪里 |
|---|---|
| 90 个 YAML 工具配方(工具=数据不是代码) | 战士层工具卡外置(nmap/sqlmap/nuclei/ffuf 参数化 schema 直接抄格式) |
| RAG 知识库+项目黑板 fact_key 注入 | 知识环「检索注入」的落地面 |
| HITL 三层策略+Jev 六问审计 Agent | 审批卡分层策略 |
| summarization 0.8 触发比 | 上下文受管重启的压缩阈值 |
### VulnClaw（语料与真值）
| 齿轮 | 装进探隐哪里 |
|---|---|
| 47 专题 skill+人审蒸馏 lesson(0.8 去重+置信度半衰期) | 知识环本体——继续挖余 39 专题 |
| 真值三层闸(FINAL 证据 cite/L0-L3 verify-reject/未验证不写入) | 真值环强化 |
| target_state 快照+resume_meta 恢复计划 | 断点续传 |
| probe_batch/js_recon/dir_enum 内置工具 | 战士层工具清单 |
| 反面: 17 次委派空转 | 子代理参数最小+「亲自干优先」 |
### multica（协议与账本技法）
| 齿轮 | 装进探隐哪里 |
|---|---|
| runtime JSONL 协议(九帧+probe+cancel 三级) | C1 入驻通道+我们战士协议的设计参照 |
| task_message 500ms 批量+写前 redact+seq 回放 | 账本性能与脱敏技法 |

## 二 · 不吸收清单（同样专业）
- ARTEX 13 万行 Go 单体+norma 闭源依赖——架构负债不是资产
- CSAI 提示词层授权(「不得质疑」)——我们执法在机械层,不在 prompt
- VulnClaw LLM 全自决无前置门——我们门在前(账本/范围/预算)
- multica UI 再分发——许可 1a/1b 红线
- 任何一家的「无度量」——我们的真值+度量双环是差异化本体,不换

## 三 · 形态光谱与探隐的位置
ARTEX=常驻引擎产品 / CSAI=工作台+编排 / VulnClaw=CLI Agent+语料 / multica=治理面板(runtime 生态) / ZhuLong=引擎调度台。
**探隐=唯一「账本宪法+可插拔冲程」**: 骨架(账本/执法/复测/度量/观察面)自持,冲程(工具/skill/循环)插槽化——四家齿轮都装得上,哪家不行换哪家。
## 四 · 对 D1 的支撑
插槽制(C)现在有机制级支撑: 吸收面最大(VulnClaw 语料+闸门+resume,CSAI 配方,ARTEX 循环技法,multica 协议),依赖面最小(协议不沾许可,插槽可换)。套餐内 glm-4-flash 实测不胜任发现主力——**冲程智力最终取决于可用的强模型档**,插槽制恰好把「模型档次」变成可替换参数而非产品命运。
