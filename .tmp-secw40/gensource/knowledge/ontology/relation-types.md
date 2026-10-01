# 本体关系类型登记（ontology/relation-types.md）

> 来源：`docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md`（安全本体与行业漏洞全集实现计划）任务2。本文件登记本体概念之间使用的关系类型，供 `ontology/concepts/` 下的概念文件和统一漏洞语义文件引用。

## 重要声明

这些关系只是**Markdown引用**，不是运行时图。GenSource不建设运行时Knowledge Graph或Traceability Graph（#34第10节已确认）。关系引用用于人工和agent理解概念之间的语义关联，不参与运行时路由、检测或事实写入。

## 关系类型表

| 关系类型 | 含义 | 典型使用场景 |
|---|---|---|
| `contains` | 包含 | 资产包含攻击面；信任边界包含入口 |
| `crosses` | 跨越 | 数据流跨越信任边界；传播路径跨越进程边界 |
| `exposes` | 暴露 | 攻击面暴露入口；服务暴露API endpoint |
| `receives_from` | 接收自 | 入口接收自数据源；Sink接收自传播路径 |
| `propagates_to` | 传播至 | 数据源传播至传播路径；传播传播至Sink |
| `transforms_to` | 转换为 | 传播过程中的数据结构变换；类型转换 |
| `stores_at` | 存储于 | 传播路径将数据存储于存储节点 |
| `guarded_by` | 被守卫保护 | Sink被Guard保护；入口被Guard保护 |
| `decided_by` | 由策略决策 | Guard的决策由Policy Decision做出 |
| `sanitized_by` | 被净化器处理 | 入口数据被Sanitizer净化；传播路径上的Sanitizer |
| `encoded_by` | 被编码器编码 | Sink前的数据被Encoder编码 |
| `reaches` | 到达 | 传播路径到达Sink；Source到达Propagation |
| `changes_state_at` | 在...处改变状态 | 传播到达状态转换节点 |
| `consumes_resource_at` | 在...处消耗资源 | 传播到达资源消耗节点 |
| `observed_by` | 被...观察 | 安全影响被可观察预言机观察 |
| `causes` | 导致 | Sink导致安全影响；状态转换导致安全影响 |
| `broader_than` | 比...更宽泛 | 统一语义之间的上下位关系 |
| `narrower_than` | 比...更狭窄 | 统一语义之间的上下位关系 |
| `variant_of` | ...的变体 | 生态映射与统一语义之间的关系 |
| `externally_mapped_to` | 外部映射至 | 本体概念与外部标准（CWE/CAPEC等）的映射 |

## 使用规范

1. 概念文件在 `## 关系` 章节引用上述关系类型，格式为表格：`| 关系类型 | 目标概念 | 说明 |`。
2. 统一漏洞语义文件在 `## 上下位语义` 和 `## 外部映射` 等章节引用上述关系类型。
3. 引用的目标必须是已登记的稳定ID（ONT-*、UVS-*等），不可引用不存在的ID。
4. 关系是单向的——`A guarded_by B` 不自动蕴含 `B guards A`，如需反向关系需显式登记或在说明中描述。
