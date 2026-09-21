# QA 三层校验与覆盖矩阵（QA_OVERRIDE_TRACKING）

> 适用范围：所有 Phase 完成后的质量校验、覆盖矩阵填充、Override 记录。
> 来源：设计文档 `2026-06-20-GenCPT-v3-design.md` 第 5.5 节（QA 三层机制）、第 8 节（漏洞验证程度）、第 9 节（合规批次策略）、第 14 节（候选编号体系）、第 15 节（确认门槛与降级规则）、第 16 节（去重仲裁规则）。
> 约束力：**强制**。第三层覆盖校验不可 override，违反将导致报告校验失败。

---

## 1. QA 三层校验框架

### 1.1 第一层：结构校验（每个 Phase 完成后）

结构校验在每个 Phase 的 MUST 输出检查点自动执行，确保数据完整性。

| 校验项 | 校验规则 | 失败处理 |
|--------|---------|---------|
| MUST 输出文件存在且非空 | 每个 Phase 对应的 `must_outputs` 文件全部存在且 size > 0 | 标记 Phase 为 incomplete，阻断后续 Phase |
| 知识图谱边引用完整 | `edges/*.json` 中每条边的 `from_node` / `to_node` 都能在 `nodes/*.json` 中找到对应节点 | 写入 `evidence/qa/qa_structure_issues.md`，需人工确认 |
| ATK-CAND 编号连续无遗漏 | ATK-CAND 从 001 起连续递增，无跳号无重复 | 写入 `evidence/qa/qa_structure_issues.md`，需补充缺失编号 |
| COMP-CAND 编号连续无遗漏 | COMP-CAND 从 001 起连续递增，无跳号无重复 | 写入 `evidence/qa/qa_structure_issues.md`，需补充缺失编号 |
| 五态标记无 `[ ]` 残留 | 最终报告前所有 `[ ]` 必须闭环为 `[x]` / `[?]` / `[-]` / `[!]` | 阻断报告生成，返回对应 Phase 补充闭环 |
| 合规判定覆盖全部规则 | `scope` 内所有平台规则均有判定结果（pass / fail / warn / na），总条数 = 规则总数 | 写入 `evidence/qa/qa_structure_issues.md`，需补充缺失判定 |
| 采集完整性 | pods.json 节点数 = SSH `kubectl get pods -A --no-headers \| wc -l`；SA/Secret/Container/Service/NetworkPolicy 同理 | 返回 Phase 1a 补采 |
| 证据完整性 | 每个 Phase 的 `raw/` 目录文件数 ≥ SSH 命令批次数 | 返回对应 Phase 补落盘 |
| 证据链完整性 | 每个 `[x]` finding 节点的 `evidence` 字段非空且指向实际文件 | 返回对应 Phase 补证据 |
| 节点字段完整性 | Pod security_context 含全部 13 字段；SA 有 secrets 字段；finding 有 evidence 字段 | 返回 Phase 1a/2 补字段 |
| 边格式一致性 | 所有边用 `attrs{}` 嵌套，强制字段在 attrs 内 | 返回对应 Phase 修正格式 |
| KG 节点引用完整性 | 所有边的 from_node/to_node 在 nodes 中存在 | 返回对应 Phase 补建节点 |

**结构校验输出**：`evidence/qa/qa_structure_check_{phase}.md`

```markdown
## QA 结构校验 — Phase {N}

- 校验时间: {timestamp}
- MUST 输出完整性: ✅/❌ ({通过数}/{总数})
- 知识图谱引用完整性: ✅/❌
- ATK-CAND 编号连续性: ✅/❌ (范围: {first}-{last})
- COMP-CAND 编号连续性: ✅/❌ (范围: {first}-{last})
- 五态标记闭环: ✅/❌ (残留 `[ ]` 数: {n})
- 合规判定覆盖率: ✅/❌ ({covered}/{total})
```

### 1.2 第二层：语义校验（Phase 8c 之前执行一次）

语义校验通过 `ssh_execute` 重新验证抽查项，度量检测结果的可信度。

| 抽查对象 | 抽查数量 | 校验方法 | 判定标准 |
|---------|---------|---------|---------|
| 合规违规项 | 随机 5 条 fail 规则 | `ssh_execute` 重新执行检测命令 | 输出与原始证据一致 → 通过 |
| ATK-CAND confirmed | 随机 3 条 | 检查差分证明逻辑自洽（攻击前/攻击后/清理可区分） | 差分证明逻辑完整 → 通过 |
| 已通过项（`[-]` / `[!])`） | 随机 2 条 | `ssh_execute` 重新验证是否真的没有风险 | 确认无风险 → 通过 |

**语义校验置信度评分**：

| 抽查结果 | 置信度 | 处理 |
|---------|--------|------|
| 全部复现 | 高 | 继续报告生成 |
| 部分不能复现 | 低 | `QA 置信度：低，建议重点复核：{条目列表}` |
| 重大偏差 | 失败 | 阻断报告，返回对应 Phase 重新检测 |

**语义校验输出**：`evidence/qa/qa_semantic_check.md`

```markdown
## QA 语义抽检报告

- 抽检时间: {timestamp}
- 合规违规抽查 (5条): {通过}/{失败}
- ATK-CAND 抽查 (3条): {通过}/{失败}
- 已通过项抽查 (2条): {通过}/{失败}
- QA 置信度: 高/低
- 建议重点复核: {条目列表（如有）}

### 抽查明细

| # | 类型 | 条目 | ATK-CAND/COMP-CAND | 复现结果 | 偏差说明 |
|---|------|------|---------------------|---------|---------|
| 1 | 合规违规 | {规则名} | COMP-CAND-{xxx} | 一致/偏差 | — |
| ... | ... | ... | ... | ... | ... |
```

**语义校验可 Override**：当环境状态发生变化（如管理员已修复）导致无法复现时，允许人工 Override 并记录。

### 1.3 第三层：覆盖校验（Phase 8c 覆盖矩阵填充）

覆盖校验确保 7 大攻击面和合规规则无盲区，**不可 Override**。

| 校验维度 | 校验规则 | 失败处理 |
|---------|---------|---------|
| 合规规则覆盖率 | 100%（226 条全有判定） | 返回 Phase 2 补缺失规则 |
| 攻击面模式覆盖率 | 100%（49 模式都有验证结论） | 返回 Phase 4a/4b 补缺失模式 |
| 五态标记闭环率 | 100%（无 `[ ]` 残留） | 返回对应 Phase 补闭环 |
| ATK-CAND 编号连续性 | 100%（无跳号无重复） | 补缺失编号 |
| 证据链完整率 | ≥90%（`[x]` 节点有 evidence 字段） | 返回对应 Phase 补证据 |
| KG 节点引用完整性 | 100%（所有边引用的节点在 nodes 中存在） | 返回对应 Phase 补建节点 |

---

## 2. Override 记录规范

### 2.1 Override 适用范围

| 层级 | 可否 Override | 说明 |
|------|-------------|------|
| 第一层：结构校验 | **不可 Override** | 每条规则都是硬性约束，缺失即失败 |
| 第二层：语义校验 | **可以 Override** | 环境变化、审批限制等原因导致无法复现时，允许人工 Override |
| 第三层：覆盖校验 | **不可 Override** | 覆盖矩阵的完整性是报告可信度的底线，不允许跳过 |

### 2.2 Override 记录格式

每次 Override 必须写入 QA 摘要报告，并单独记录到 `evidence/qa/qa_override_{phase}.md`。

**Override 记录模板**：

```markdown
## QA Override 记录 — Phase {N}

### Override #{seq}

| 字段 | 值 |
|------|-----|
| override_reason | {Override 原因，详述为何无法复现或为何原判定需修正} |
| override_by | {操作人/Agent 标识，如 "supervisory-agent" 或 "手动确认"} |
| override_date | {ISO 8601 时间戳} |
| original_value | {原始判定值，如 "fail → K8s-5.2.1 特权容器"} |
| overridden_value | {Override 后值，如 "warn → 已在测试间修复"} |
| evidence_reference | {支撑 Override 的证据文件路径或 SSH 输出摘要} |
| verification_attempt | {重新验证的尝试记录和结果} |
```

### 2.3 Override 规则

1. **只有第二层可以人工 Override**：结构校验和覆盖校验的失败不可 Override。
2. **Override 不可绕过第三层**：即使 Override 了语义校验的某项，覆盖矩阵仍必须完整填写。
3. **Override 必须进入 QA 摘要报告**：所有 Override 记录汇总到 `evidence/qa/qa_summary_report.md` 的 Override 列表章节。
4. **Override 数量上限**：同一 Phase 内 Override > 3 条 → QA 置信度降为低。
5. **Override 不可用于跳过检测**：Override 只能用于修正判定结果（如 fail → warn），不能用于将"未检测"标记为"不可利用"。

### 2.4 Override 产生时机

Override 记录在以下场景产生：

| 场景 | 产生方式 | 记录位置 |
|------|---------|---------|
| Phase 4 实际命中质检员标记为"通过"的规则 | 回溯验证自动生成 | `evidence/qa/qa_override_phase4.md` |
| 语义抽检无法复现但环境已变化 | 人工确认后记录 | `evidence/qa/qa_semantic_check.md`（追加） |
| 审批门控被拒绝导致攻击路径中断 | 降级处理时记录 | `evidence/qa/qa_override_phase4.md` |

---

## 3. 覆盖矩阵格式

### 3.1 攻击面覆盖矩阵

行：7 大攻击面（AS-1 至 AS-7），每个攻击面展开为子类型。
列：验证来源（模式库命中 / LLM 推理 / 总覆盖）。

**矩阵模板**：

```markdown
## 攻击面覆盖矩阵

| 攻击面 | 子类型 | 模式库覆盖 | LLM 推理覆盖 | 验证等级 | ATK-CAND 编号 | 备注 |
|--------|--------|-----------|-------------|---------|--------------|------|
| **AS-1 逃逸** | | | | | | |
| AS-1.1 | docker.sock 挂载逃逸 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-1.2 | privileged 容器逃逸 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-1.3 | cgroup 逃逸 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-1.4 | runc 逃逸 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-1.5 | hostPath 挂载逃逸 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-1.6 | capability 提权逃逸 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-1.7 | procfs 逃逸 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| **AS-2 认证授权** | | | | | | |
| AS-2.1 | ServiceAccount Token 滥用 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-2.2 | RBAC 越权 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-2.3 | kubelet 匿名访问 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-2.4 | etcd 未认证访问 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| **AS-3 网络** | | | | | | |
| AS-3.1 | 横向移动 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-3.2 | NTFS/ALPN 异常 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-3.3 | 云元数据 API 访问 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-3.4 | DNS 数据外泄 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| **AS-4 数据泄露** | | | | | | |
| AS-4.1 | Secret 窃取 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-4.2 | 环境变量凭据泄露 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-4.3 | 镜像层 Secret 泄露 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| **AS-5 拒绝服务** | | | | | | |
| AS-5.1 | 资源滥用 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-5.2 | Fork Bomb | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| **AS-6 供应链** | | | | | | |
| AS-6.1 | 镜像标签篡改 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-6.2 | 仓库投毒 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| **AS-7 持久化** | | | | | | |
| AS-7.1 | Webhook 后门 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-7.2 | CronJob 持久化 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
| AS-7.3 | Docker Volume 持久化 | ✅/❌ | ✅/❌ | C1/C2/C3/不可利用/未检测 | ATK-CAND-xxx | |
```

### 3.2 验证等级定义

| 验证等级 | 标记 | 含义 | 证据要求 |
|---------|------|------|---------|
| C1 实证复现 | ✅✅ | 实际执行攻击路径，差分证明成功 | 5 项门槛全满足 + L2 执行上下文差分证明 |
| C2 条件实证 | ✅ | 前置条件全部满足，理论链路完整 | 前置条件全部列举 + 理论链路清晰 + 不可复现原因 |
| C3 风险线索 | ⚠️ | 配置存在安全隐患但前置条件不完全满足 | 配置证据 + 风险分析 + 建议补充验证 |
| 不可利用 | ➖ | 已检查，前置条件不满足 | 至少有 L0 的证伪依据 |
| 已阻断 | 🛑 | 被安全机制阻断 | 至少有 L1 的阻断证据 |
| 未检测 | ❓ | 当前 Phase 未覆盖此攻击面/子类型 | 必须注明原因和建议补充 |

### 3.3 "不可利用" 标注规则

矩阵中出现"不可利用"时，**必须**附带证伪依据：

```markdown
| AS-x.y | {子类型名} | ❌ | ❌ | 不可利用 ➖ | ATK-CAND-xxx | 证伪依据: {L0+ 命令输出证明前置条件不满足} |
```

证伪依据要求：
- 至少包含 L0（宿主机观察）级别的 SSH 输出
- 明确指出哪个前置条件不满足
- 证伪命令和输出必须真实（来自 `ssh_execute`），禁止编造

### 3.4 "未检测" 标注规则

矩阵中出现"未检测"时，**必须**注明原因和建议补充：

```markdown
| AS-x.y | {子类型名} | ❌ | ❌ | 未检测 ❓ | — | 原因: {环境限制/审批限制/模式库缺失} | 建议补充: {具体建议} |
```

常见原因分类：
- **环境限制**：目标环境无对应组件（如无 K8s 则 AS-7.1 Webhook 后门不适用）
- **审批限制**：L4/L5 操作被拒绝，降级为 C2 条件实证
- **模式库缺失**：`_index.md` 和 `_learned/` 中均无匹配模式且 LLM 推理未覆盖
- **工具不可用**：目标环境无所需验证工具且无法上传

---

## 4. 合规覆盖矩阵

### 4.1 矩阵格式

行：CIS Benchmark 分组（K8s 29 组 + Docker 7 组 + Containerd 5 组）。
列：合规检测状态 + COMP-CAND 编号。

```markdown
## 合规覆盖矩阵

### K8s 合规（29 组 / 134 条）

| CIS 分组 | 规则数 | pass | fail | warn | na | fail COMP-CAND | 关联攻击假设 |
|----------|--------|------|------|------|----|----------------|-------------|
| G_1_1 API Server 文件权限 | 7 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1/AS-2 |
| G_1_2 API Server 认证授权 | 23 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-2 |
| G_1_3 API Server DoS 防护 | 1 | {n} | {n} | {n} | {n} | — | AS-5 |
| G_1_4 API Server 信息泄露防护 | 3 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-4 |
| G_1_5 API Server 审计日志 | 6 | {n} | {n} | {n} | {n} | — | AS-7 |
| G_1_6 API Server SSL/TLS | 1 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-2/AS-4 |
| G_2_1 Etcd 文件权限 | 4 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1 |
| G_2_2 Etcd 配置 | 2 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-4 |
| G_2_3 Etcd 安全配置 | 4 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-2 |
| G_2_4 Etcd 网络隔离 | 1 | {n} | {n} | {n} | {n} | — | AS-5 |
| G_3_1 Controller Manager 安全 | 4 | {n} | {n} | {n} | {n} | — | — |
| G_3_2 Scheduler 安全 | 2 | {n} | {n} | {n} | {n} | — | AS-4 |
| G_4_1 Kubelet 认证 | 4 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-2 |
| G_4_2 Kubelet 授权配置 | 7 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-2 |
| G_4_3 Kubelet 配置文件权限 | 1 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1 |
| G_5_1 Kubelet 运行时配置 | 8 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1 |
| G_5_2 Kubelet 流式连接 | 6 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-2 |
| G_5_3 Kubelet TLS 配置 | 2 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-4 |
| G_5_4 Kubelet 信息泄露防护 | 5 | {n} | {n} | {n} | {n} | — | AS-4/AS-5 |
| G_5_5 Kubelet DoS 防护 | 1 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-5 |
| G_5_6 Kubelet 系统配置 | 1 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-2 |
| G_6_1 Network Policies | 2 | {n} | {n} | {n} | {n} | — | AS-3 |
| G_6_2 Network Default Deny | 1 | {n} | {n} | {n} | {n} | — | AS-3 |
| G_7_1 Pod Security | 15 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1/AS-2/AS-7 |
| G_7_2 Container Runtime | 2 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-2 |
| G_8_1 Secret 管理 | 2 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-4 |
| G_8_2 RBAC 配置 | 13 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-2/AS-7 |
| G_8_3 Security Context | 2 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1/AS-4 |
| G_8_4 Network Policies Advanced | 4 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-3 |
| **K8s 合计** | **134** | **{n}** | **{n}** | **{n}** | **{n}** | — | — |

### Docker 合规（7 组 / 64 条）

| CIS 分组 | 规则数 | pass | fail | warn | na | fail COMP-CAND | 关联攻击假设 |
|----------|--------|------|------|------|----|----------------|-------------|
| G_1 运行环境配置 | 5 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1 |
| G_2 守护进程参数 | 11 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1/AS-2 |
| G_3 文件权限 | 10 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1 |
| G_4 镜像构建 | 7 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-6 |
| G_5 容器运行时 | 26 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1/AS-7 |
| G_6 容器运维 | 2 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-3 |
| G_7 集群配置 | 3 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1/AS-2 |
| **Docker 合计** | **64** | **{n}** | **{n}** | **{n}** | **{n}** | — | — |

### Containerd 合规（5 组 / 28 条）

| CIS 分组 | 规则数 | pass | fail | warn | na | fail COMP-CAND | 关联攻击假设 |
|----------|--------|------|------|------|----|----------------|-------------|
| G_1 运行环境配置 | 3 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1 |
| G_2 守护进程参数 | 3 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1/AS-7 |
| G_3 文件权限 | 10 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-1 |
| G_4 镜像构建 | 2 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-6 |
| G_5 容器运行时 | 10 | {n} | {n} | {n} | {n} | COMP-CAND-xxx | AS-3 |
| **Containerd 合计** | **28** | **{n}** | **{n}** | **{n}** | **{n}** | — | — |
```

### 4.2 fail / warn 关联规则

每个 fail 或 warn 状态**必须**关联攻击假设：

```markdown
## COMP-CAND 关联映射

| COMP-CAND | CIS 规则 | 判定 | 关联 ATK-CAND | 攻击假设 | 映射来源 |
|-----------|---------|------|--------------|---------|---------|
| COMP-CAND-001 | K8s-5.2.1 | fail | ATK-CAND-xxx | 特权容器逃逸 | compliance-hypotheses.md |
| COMP-CAND-002 | K8s-5.2.3 | fail | ATK-CAND-xxx | docker.sock 逃逸 | compliance-hypotheses.md |
```

映射来源取值：
- `compliance-hypotheses.md`：三库联动中的合规假设库预定义映射
- `cross-ref`：Phase 3 交叉关联发现的新映射
- `attack-pattern`：Phase 4a 模式库命中的映射

---

## 5. 去重 5 键

### 5.1 去重键定义

攻击结果去重使用以下 5 键组合：

| 键 | 说明 | 示例 |
|----|------|------|
| host_fingerprint | 主机唯一标识（主机名 + IP + 容器运行时版本的 hash） | `k8s-node-01_10.0.1.5_containerd://1.6.20` |
| attack_surface | 攻击面编号 | `AS-1.1` |
| vulnerability_type | 漏洞类型 | `docker_sock_escape` |
| attack_vector | 攻击向量（具体攻击路径） | `docker_sock_mount_privileged_container` |
| verification_level | 验证等级 | `C1` / `C2` / `C3` |

**去重 5 键完整格式**：

```
host_fingerprint + attack_surface + vulnerability_type + attack_vector + verification_level
```

### 5.2 去重执行时机

| 时机 | 去重范围 | 策略 |
|------|---------|------|
| Phase 4a（攻击模式匹配） | 同一攻击面内不同模式命中的相同漏洞 | 相同 5 键 → 保留最新 timestamp，源标记取并集（📚+🧠→标注多源） |
| Phase 5（攻击链构建前） | 所有 Phase 数据合并后的全局去重 | 相同 5 键 → 保留最新 timestamp，合并证据和 edges |
| Phase 8（报告生成前） | 最终去重，消除 Phase 间累积的重复 | 相同 5 键 → 保留最新 timestamp，finding 的 sources 字段取并集 |

### 5.3 去重策略细则

| 场景 | 策略 |
|------|------|
| 相同 5 键，不同验证等级 | 保留最高验证等级（C1 > C2 > C3），删除低等级 |
| 相同 5 键，不同来源（📚/🧠/🔄） | 合并为多源标记，sources 字段取并集 |
| 相同 5 键，不同 ATK-CAND | 保留先创建的 ATK-CAND 编号，合并证据 |
| 知识图谱节点 id 冲突 | 保留最新 timestamp；字段互补 → 取并集 |
| 知识图谱边冲突 | from_node + to_node + edge_type 相同 → 保留最新 timestamp |
| 交叉关联边语义重复 | from_node + to_node + reason 语义 hash → 避免文字略异的重复关联 |

---

## 6. QA Summary Report 格式

QA 摘要报告在 Phase 8c 生成，位于 `evidence/qa/qa_summary_report.md`。

### 6.1 报告结构

```markdown
# QA Summary Report

## 1. 执行概览

- 测试会话: {session_dir}
- 测试模式: {A/B/C}
- 目标平台: {scope}
- 测试时间: {start} — {end}
- QA 执行时间: {timestamp}

## 2. 结构校验结果

| Phase | MUST 输出 | 图谱引用 | ATK-CAND 连续性 | COMP-CAND 连续性 | 五态闭环 | 合规覆盖 | 结果 |
|-------|----------|---------|----------------|-----------------|---------|---------|------|
| 1 | ✅/❌ | ✅/❌ | — | — | ✅/❌ | — | 通过/失败 |
| 2 | ✅/❌ | ✅/❌ | — | ✅/❌ | ✅/❌ | ✅/❌ | 通过/失败 |
| 3 | ✅/❌ | ✅/❌ | — | ✅/❌ | ✅/❌ | — | 通过/失败 |
| 4 | ✅/❌ | ✅/❌ | ✅/❌ | — | ✅/❌ | — | 通过/失败 |
| 5 | ✅/❌ | ✅/❌ | ✅/❌ | — | ✅/❌ | — | 通过/失败 |
| 6 | ✅/❌ | ✅/❌ | ✅/❌ | — | ✅/❌ | — | 通过/失败 |
| 7 | ✅/❌ | ✅/❌ | ✅/❌ | — | ✅/❌ | — | 通过/失败 |
| 8 | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | 通过/失败 |

**结构校验总评**: ✅ 全部通过 / ❌ {N} 项失败

## 3. 语义校验结果

- 合规违规抽查: {通过}/{总数}
- ATK-CAND 抽查: {通过}/{总数}
- 已通过项抽查: {通过}/{总数}
- QA 置信度: 高 / 低
- 建议重点复核: {条目列表}

## 4. 覆盖矩阵完成率

### 4.1 攻击面覆盖矩阵完成率

| 攻击面 | 子类型总数 | 已覆盖 | 不可利用 | 未检测 | 完成率 |
|--------|-----------|-------|---------|-------|--------|
| AS-1 逃逸 | {n} | {n} | {n} | {n} | {n}% |
| AS-2 认证授权 | {n} | {n} | {n} | {n} | {n}% |
| AS-3 网络 | {n} | {n} | {n} | {n} | {n}% |
| AS-4 数据泄露 | {n} | {n} | {n} | {n} | {n}% |
| AS-5 拒绝服务 | {n} | {n} | {n} | {n} | {n}% |
| AS-6 供应链 | {n} | {n} | {n} | {n} | {n}% |
| AS-7 持久化 | {n} | {n} | {n} | {n} | {n}% |
| **合计** | **{n}** | **{n}** | **{n}** | **{n}** | **{n}%** |

**攻击面覆盖总完成率: {n}%**（需 100%）

### 4.2 合规覆盖矩阵完成率

| 平台 | 规则总数 | pass | fail | warn | na | fail 数 (COMP-CAND) | 无关联假设的 fail | 完成率 |
|------|---------|------|------|------|----|--------------------|-------------------|--------|
| K8s | 134 | {n} | {n} | {n} | {n} | {n} | {n} | {n}% |
| Docker | 64 | {n} | {n} | {n} | {n} | {n} | {n} | {n}% |
| Containerd | 28 | {n} | {n} | {n} | {n} | {n} | {n} | {n}% |
| **合计** | **226** | **{n}** | **{n}** | **{n}** | **{n}** | **{n}** | **{n}** | **{n}%** |

**合规覆盖总完成率: {n}%**（需 100%）

## 5. Override 列表

| # | Phase | Override 原因 | 原始值 | Override 后值 | Override 人 | Override 日期 | 证据引用 |
|---|-------|--------------|--------|--------------|------------|--------------|---------|
| 1 | {phase} | {reason} | {original} | {overridden} | {by} | {date} | {ref} |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Override 统计**: 共 {N} 条 override，{N > 3 ? "超过 3 条，QA 置信度降为低" : "不超过 3 条"}

## 6. 不可利用项汇总

| # | ATK-CAND | 攻击面 | 子类型 | 证伪依据 | 证伪层级 | 证伪命令 |
|---|----------|--------|--------|---------|---------|---------|
| 1 | ATK-CAND-xxx | AS-{n} | {子类型名} | {前置条件不满足的具体说明} | L0/L1 | `{命令}` → `{输出摘要}` |
| ... | ... | ... | ... | ... | ... | ... |

**不可利用项数量**: {N} 项

## 7. 最终判定

- 结构校验: ✅ 通过 / ❌ 失败
- 语义校验: ✅ 通过（置信度: 高/低）/ ❌ 失败
- 覆盖校验: ✅ 通过 / ❌ 失败
- Override 数量: {N} 条（{是否超过 3 条}）
- 报告可行: ✅ 是 / ❌ 否（需返回修复）
```

### 6.2 小结字段说明

| 字段 | 计算方式 |
|------|---------|
| 攻击面覆盖完成率 | `(已覆盖 + 不可利用) / 子类型总数 × 100%`，目标 100% |
| 合规覆盖完成率 | `(有判定结果的规则数) / 规则总数 × 100%`，目标 100% |
| Override 统计 | 所有 Phase 的 override 记录汇总，> 3 条则 QA 置信度降为低 |
| 不可利用项 | 必须每项附带 L0+ 证伪依据和 SSH 命令输出 |
| 最终判定 | 三层校验全部通过 + Override ≤ 3 → 报告可行；任一层失败 → 返回修复 |

---

## 7. 五态标记与 QA 校验交互

五态标记系统（5.1 节）与 QA 三层校验紧密交互：

| 五态标记 | QA 校验要求 | 覆盖矩阵对应 |
|---------|-----------|-------------|
| `[x]` 存在明确候选 | 必须生成 ATK-CAND 并完成验证闭环 | 验证等级 C1/C2/C3 |
| `[?]` 存在可疑面 | 交给 Phase 4b 处理，最终必须转为其他态 | 验证等级 C3 或降级 |
| `[-]` 已证伪 | 必须写明证伪依据（≥L0 命令输出） | 覆盖矩阵"不可利用"行 |
| `[!]` 已阻断 | 必须写明阻断机制名称 | 验证等级 C2（条件实证） |
| `[ ]` 过程态 | **最终报告前必须消灭，不能留空** | — |

**闭环规则**：
1. 所有 ATK-CAND 必须闭环：确认（C1/C2/C3）/ 降级为高风险线索 / 放弃
2. 所有 COMP-CAND 必须闭环：pass / fail / warn / na
3. 五态标记从 `[ ]` 转变必须有证据支撑，不得无凭据标记为 `[-]` 或 `[!]`
4. `[?]` 在 Phase 4b 处理后必须转为确定态