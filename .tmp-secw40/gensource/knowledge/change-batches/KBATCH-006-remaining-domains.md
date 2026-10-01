# KBATCH-006：剩余域可执行知识建设（44 UVS）

> 变更批次记录：2026-08-09，为14个剩余域的44个UVS建设可执行知识。

## 批次概述

| 维度 | 描述 |
|---|---|
| 批次ID | KBATCH-006 |
| 日期 | 2026-08-09 |
| 范围 | 14个域的44个UVS可执行知识建设 |
| 引用分级 | 全部Proposed/Inferred（基于行业标准转译，待实测验证） |
| 前置批次 | KBATCH-001种子迁移、KBATCH-002注入域、访问控制域、并发/异常/计算/保护域、内存/文件/输入域、资源/控制流/信息域 |

## 建设内容

### 按域统计

| 域 | UVS数 | vuln-patterns | attack-patterns | fix-patterns |
|---|---:|---:|---:|---:|
| 硬件安全（HW） | 7 | 7 | 7 | 7 |
| 代码（CODE） | 7 | 7 | 7 | 7 |
| AI | 5 | 5 | 5 | 5 |
| 域/隔离（SPHERE） | 7 | 7 | 7 | 7 |
| UI | 3 | 3 | 3 | 3 |
| 交互（INTERACTION） | 3 | 3 | 3 | 3 |
| 供应链（SUPPLY） | 2 | 2 | 2 | 2 |
| 状态（STATE） | 2 | 2 | 2 | 2 |
| 物理（PHYSICAL） | 2 | 2 | 2 | 2 |
| 类型/命名（TYPE/NAME） | 2 | 2 | 2 | 2 |
| 进程（PROCESS） | 1 | 1 | 1 | 1 |
| 日志（LOGGING） | 1 | 1 | 0（不适用） | 1 |
| 封装（ENCAPSULATION） | 1 | 1 | 1 | 1 |
| 编码（ENCODING） | 1 | 1 | 1 | 1 |
| **合计** | **44** | **44** | **43** | **44** |

### 特殊模型使用

- 硬件域使用Memory/Privilege/Physical Interface/Firmware模型
- AI域使用Instruction/Data/Tool/Memory/Trust模型
- 球体/隔离域使用Trust Boundary/Sphere/Channel模型

### 攻击模式不适用说明

- UVS-LOGGING-INSUFFICIENT：防御监控缺口，无独立活攻击面（与UVS-PROT-ADMIN-CONTROL-FAILURE的dead-control处理一致）

## 质量要求达成

- 每个vuln-pattern含逐步可执行发现步骤、正例、负例、排除条件
- 未复制CWE摘要——所有内容基于UVS语义根因/不变量/本体路径重新编写
- 覆盖矩阵已更新（14个域覆盖文件+汇总索引）
- 三个知识库索引（vuln-patterns/attack-patterns/fix-patterns）已追加条目

## 覆盖矩阵更新

| 域 | discoverable | verifiable | exploit_model | remediable | ecosystem | validated |
|---|---|---|---|---|---|---|
| 全部14个域 | complete | complete | complete（logging为not_applicable） | complete | partial | not_started |

## 文件清单

- vuln-patterns/：44个新条目
- attack-patterns/：43个新条目
- fix-patterns/：44个新条目
- coverage/semantic-capability/：14个覆盖文件更新+_index.md汇总更新
- 三个_index.md索引文件追加条目

## 来源与证据

- 证据来源：行业标准转译（CWE/CAPEC/OWASP）
- 引用分级：Proposed（vuln-patterns/attack-patterns默认）、Inferred（fix-patterns默认、部分attack-patterns）
- 证据局限：全部为基于行业标准的推导，未经GenSource实测验证
