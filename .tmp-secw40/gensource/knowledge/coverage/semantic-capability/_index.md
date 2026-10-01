# 能力覆盖矩阵（coverage/semantic-capability/_index.md）

> 来源：`docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md`（安全本体与行业漏洞全集实现计划）任务7。本文件是八维能力覆盖矩阵的汇总索引。

## 禁止声明

**名称映射不等于检测能力。cataloged只表示条目已进入目录，不表示可发现或可验证。**

> 禁止由名称映射自动推导检测能力。一个UVS被cataloged和modeled仅表示其语义模型已建立，不表示GenSource能自动发现、验证或修复该类问题。discoverable/verifiable/exploit_model_available/remediable/ecosystem_mapped/validated六个维度反映的是可执行知识层的建设状态，需通过vuln-patterns、attack-patterns、fix-patterns、ecosystem-mappings等条目的逐步创建来升级。

## 用途

语义能力覆盖矩阵追踪每个统一漏洞语义在八个维度上的能力状态。第3部分可执行知识建设完成后，各维度状态将逐步从not_started升级为complete。

## 八维能力

| 维度 | 含义 | 达到complete的要求 |
|---|---|---|
| cataloged | 已编目 | UVS已建立且来源对账完成 |
| modeled | 已建模 | 本体路径/根因/不变量/正反例齐备 |
| discoverable | 可发现 | 存在可执行发现模式（vuln-patterns条目） |
| verifiable | 可验证 | 存在确认与反证方法（verification能力可消费） |
| exploit_model_available | 攻击模型可用 | 存在攻击模型（attack-patterns条目） |
| remediable | 可修复 | 存在标准修复模式（fix-patterns条目） |
| ecosystem_mapped | 生态已映射 | 存在生态映射（ecosystem-mappings条目） |
| validated | 已验证 | 有实证证据（实测案例/外部验证） |

状态只允许：`complete` / `partial` / `not_started` / `not_applicable` / `blocked`。
`not_applicable`和`blocked`必须有理由及证据引用。

## 域统计汇总

| 域文件 | 域名称 | UVS数 | cataloged | modeled | discoverable | verifiable | exploit | fix | ecosystem | validated |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| access-control | 访问控制 | 15 | 15 | 15 | 13 | 15 | 14 | 14 | 0 | 0 |
| injection | 注入 | 12 | 12 | 12 | 12 | 12 | 11 | 11 | 0 | 0 |
| hardware | 硬件安全 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 0 | 0 |
| code | 代码 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 0 | 0 |
| ai | AI | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 0 | 0 |
| sphere | 域/隔离 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 0 | 0 |
| ui | UI | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 0 | 0 |
| interaction | 交互 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 0 | 0 |
| supply-chain | 供应链 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 0 | 0 |
| state | 状态 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 0 | 0 |
| physical | 物理 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 0 | 0 |
| type-naming | 类型/命名 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 0 | 0 |
| process | 进程 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| logging | 日志 | 1 | 1 | 1 | 0 | 1 | 0 | 1 | 0 | 0 |
| encapsulation | 封装 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| encoding | 编码 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| input | 输入验证 | 9 | 9 | 9 | 9 | 9 | 8 | 9 | 0 | 0 |
| crypto | 密码学 | 9 | 9 | 9 | 9 | 9 | 9 | 9 | 0 | 1 |
| memory | 内存 | 5 | 5 | 5 | 4 | 5 | 5 | 5 | 0 | 0 |
| information | 信息泄露 | 7 | 7 | 7 | 5 | 7 | 3 | 7 | 0 | 0 |
| control-flow | 控制流 | 7 | 7 | 7 | 7 | 7 | 2 | 6 | 0 | 0 |
| resource | 资源生命周期 | 15 | 15 | 15 | 15 | 15 | 6 | 14 | 0 | 0 |
| protection | 保护机制 | 6 | 6 | 6 | 6 | 6 | 4 | 5 | 0 | 0 |
| file | 文件 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 0 | 0 |
| exception | 异常处理 | 4 | 4 | 4 | 4 | 4 | 3 | 3 | 0 | 0 |
| calc | 计算 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 0 | 0 |
| concurrency | 并发 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 0 | 0 |
| **合计** | — | **145** | **145** | **145** | **138** | **145** | **120** | **139** | **0** | **1** |

> 注：汇总数只统计`complete`，`partial`和`not_applicable`不并入。按分片行机械重算：exploit为120 complete、3 partial、22 not_applicable；fix为139 complete、3 partial、3 not_applicable；ecosystem为0 complete、126 partial、19 not_started（模式乘框架级生态映射约169条待创建，不把已有15个语言/框架级ECMAP文件误述为模式级已覆盖）；discoverable为138 complete、7 信号级（SENSITIVE-EXPOSE/LOGGING/AUTHN-BYPASS/BRUTE-FORCE/OBSERVABLE-DIFF/STATE-CONCURRENT/MEM-INDEX 命中仅作浅扫过滤，不逐条进 sink_inventory，标“信号级（不进实例清单）”）；validated为1 complete、144 not_started——当前仅 1 个 UVS 有靶场实测（dvpwa，UVS-CRYPTO-WEAK-ALGORITHM），其余 4 个 dvpwa 种子（sql-injection-string-concat、template-autoescape-disabled-xss、missing-authorization-check、dead-security-control）待提升。KBATCH-001至KBATCH-006累计建设148个vuln-patterns、120个attack-patterns、141个fix-patterns，覆盖全部27个域145个UVS。


## 分片文件

- [access-control.md](access-control.md)（访问控制，15个UVS）
- [injection.md](injection.md)（注入，12个UVS）
- [input.md](input.md)（输入验证，9个UVS）
- [crypto.md](crypto.md)（密码学，9个UVS）
- [memory.md](memory.md)（内存，5个UVS）
- [sphere.md](sphere.md)（域/隔离，7个UVS）
- [information.md](information.md)（信息泄露，7个UVS）
- [hardware.md](hardware.md)（硬件安全，7个UVS）
- [code.md](code.md)（代码，7个UVS）
- [control-flow.md](control-flow.md)（控制流，7个UVS）
- [resource.md](resource.md)（资源生命周期，15个UVS）
- [protection.md](protection.md)（保护机制，6个UVS）
- [file.md](file.md)（文件，6个UVS）
- [ai.md](ai.md)（AI，5个UVS）
- [exception.md](exception.md)（异常处理，4个UVS）
- [calc.md](calc.md)（计算，4个UVS）
- [ui.md](ui.md)（UI，3个UVS）
- [interaction.md](interaction.md)（交互，3个UVS）
- [supply-chain.md](supply-chain.md)（供应链，2个UVS）
- [state.md](state.md)（状态，2个UVS）
- [physical.md](physical.md)（物理，2个UVS）
- [concurrency.md](concurrency.md)（并发，2个UVS）
- [type-naming.md](type-naming.md)（类型/命名，2个UVS）
- [process.md](process.md)（进程，1个UVS）
- [logging.md](logging.md)（日志，1个UVS）
- [encapsulation.md](encapsulation.md)（封装，1个UVS）
- [encoding.md](encoding.md)（编码，1个UVS）

## 模板

编写覆盖记录时参考 [\_templates/semantic-capability-template.md](../../_templates/semantic-capability-template.md)。

## 消费方

- `scope-and-context`：范围与威胁语境能力引用覆盖状态披露知识缺口
- `candidate-discovery`：候选发现能力引用discoverable状态
- `verification-and-rating`：验证与定级能力引用verifiable状态
- `remediation-guidance`：修复指导能力引用remediable状态
- `report-delivery`：报告交付能力引用覆盖矩阵披露检测能力边界
