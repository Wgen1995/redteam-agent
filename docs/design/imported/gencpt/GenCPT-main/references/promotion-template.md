# 攻击模式晋升模板

本文档提供晋升新攻击模式时使用的 SKILL.md 模板和 8 段格式规范。当 LLM 推理发现满足晋升门槛（参见 `promotion-criteria.md`）时，按照此模板生成新模式文件。

---

## 1. Frontmatter 模板

新晋升的模式使用以下 frontmatter：

```yaml
---
source: learned                    # 来源标识：learned（LLM 推理晋升）
confidence: medium                 # 初始置信度：medium（learned 模式初始值）
platforms: [k8s]                   # 适用平台：k8s / docker / containerd 及其组合
mapped_attack_surfaces: [AS-1]     # 映射攻击面：AS-1 到 AS-7 的子类型
mapped_compliance_families: [特权容器] # 映射合规族：关联的 CIS 分组
required_tools: []                 # 所需工具：原生命令足够则留空
execution_contexts: [L0, L1, L2]  # 涉及的执行上下文层级
max_verification_level: L2         # 最高验证层级：L0/L1/L2/L3
destructive: false                 # 是否破坏性操作：true 时最高 L3（条件验证）
hit_count: 1                       # 累计命中次数（learned 模式从 1 开始）
last_hit: 2026-06-20               # 最后命中日期
promoted_date: 2026-06-20          # 晋升日期
created_from: insights.md          # 来源文件（insights.md 中的条目 ID）
---
```

### Frontmatter 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source` | enum | 是 | `manual`（人工编写）/ `curated`（策略审核）/ `learned`（LLM 晋升） |
| `confidence` | enum | 是 | `high`（manual/curated）/ `medium`（learned 初始值）/ `stale`（降级后） |
| `platforms` | list | 是 | 适用平台列表，取值：`k8s`、`docker`、`containerd` |
| `mapped_attack_surfaces` | list | 是 | 映射的攻击面子类型，如 `AS-1.1`、`AS-2.3` |
| `mapped_compliance_families` | list | 是 | 关联的 CIS 合规族名称 |
| `required_tools` | list | 否 | 所需工具列表，原生命令足够则留空 |
| `execution_contexts` | list | 是 | 该模式涉及的执行上下文层级：`L0`/`L1`/`L2`/`L3` |
| `max_verification_level` | enum | 是 | 该模式最高可达到的验证层级 |
| `destructive` | boolean | 是 | 是否包含破坏性操作（`true` 时最高验证 L3） |
| `hit_count` | integer | 是 | 累计命中次数 |
| `last_hit` | date | 是 | 最后命中日期（YYYY-MM-DD） |
| `promoted_date` | date | 是 | 晋升日期（仅 learned 模式） |
| `created_from` | string | 是 | 来源文件标识 |

> **字段适用范围说明**：`source`、`confidence`、`platforms`、`mapped_attack_surfaces`、`mapped_compliance_families`、`required_tools`、`execution_contexts`、`max_verification_level`、`destructive` 共 9 个字段为基础字段，所有模式（manual/curated/learned）均需填写。`hit_count`、`last_hit` 为 learned 模式特有字段（用于自净和降级判定），manual/curated 模式不需要。`promoted_date`、`created_from` 仅 learned 模式需要。实际 manual/curated 模式文件的 9 个 frontmatter 字段即为基础字段。

### required_tools 子项格式

当需要工具时，按以下格式填写：

```yaml
required_tools:
  - name: cdk                             # 工具名称
    transform_commands:                    # 该模式使用的子命令
      - "cdk evaluate"
      - "cdk run check-docker-socket"
    fallback_native: |                    # 无工具时的原生命令降级方案（必填）
      ls -la /var/run/docker.sock
      cat /proc/1/cgroup | head -1
      mount | grep docker
```

---

## 2. 8 段格式骨架

每个攻击模式 SKILL.md 必须包含以下 8 个章节，顺序固定，不可遗漏：

### 第 1 段：前置条件

```markdown
## 1. 前置条件

这个攻击模式需要什么条件才能触发。列举所有必需的前置条件，每个条件标注检测方式。

### 环境要求
- 目标平台：[k8s/docker/containerd]
- 攻击者上下文：[容器内 / 宿主机级别]
- 目标服务版本范围：[如 K8s ≤ 1.28 / Docker ≤ 24.x]

### 必要条件（全部满足才可触发）
1. [条件 1 描述] → 检测命令：`[L0/L1] command`
2. [条件 2 描述] → 检测命令：`[L0/L1] command`
3. [条件 N 描述] → 检测命令：`[L0/L1] command`

### 增强（非必要但影响成功率）
1. [增强条件 1] → 检测命令：`[L0/L1] command`
```

**编写要求**：
- 必要条件必须全部满足才能触发攻击
- 每个条件提供检测命令和期望输出
- 检测命令标注执行上下文层级（L0/L1）
- 不使用模糊描述（如"等"、"..."）

### 第 2 段：探测命令

```markdown
## 2. 探测命令

验证前置条件的命令列表，每步标注执行上下文（L0/L1）。

### 步骤 1：[探测目标 1]
- [L0] `command` → 期望输出：[描述]
- [L1] `command` → 期望输出：[描述]

### 步骤 2：[探测目标 2]
- [L0] `command` → 期望输出：[描述]
- [L1] `command` → 期望输出：[描述]
```

**编写要求**：
- 探测命令全部为可实际执行的 SSH/kubectl 命令
- 每条命令标注执行上下文层级
- 每条命令标注期望输出
- 优先使用原生命令（kubectl/docker/crictl/shell 内置）
- 不含占位符，全部为实际命令

### 第 3 段：攻击验证

```markdown
## 3. 攻击验证

满足前置条件后，验证攻击可行性的步骤，每步标注执行上下文（L1/L2/L3）。

### 验证步骤
- [L2] `attack_command_1` → 期望输出：[攻击成功指标]
- [L2] `attack_command_2` → 期望输出：[攻击成功指标]
- [L2] `cleanup_command` → 清理临时资源

### 破坏性操作标注
- 本模式 [包含/不包含] 破坏性操作
- 如包含：标注为 L3 条件验证，不实际执行
```

**编写要求**：
- 攻击验证标注 L2（容器内攻击验证）或 L3（条件验证）
- 破坏性操作只做条件验证，不实际执行
- 所有临时资源必须有清理步骤
- 遵守安全红线：不含持久化、不影响生产可用性

### 第 4 段：差分证明

```markdown
## 4. 差分证明

攻击前状态 vs 攻击后状态对比，每步标注执行上下文。
明确列出"什么变化证明攻击成功"。至少包含 2 个可观测差异。

### 攻击前状态
- [L0] `before_command_1` → 输出：[baseline 状态 1]
- [L1] `before_command_2` → 输出：[baseline 状态 2]

### 攻击后状态
- [L0] `after_command_1` → 输出：[变化状态 1]
- [L1] `after_command_2` → 输出：[变化状态 2]

### 差分总结
1. [差异点 1]：[攻击前] → [攻击后]
2. [差异点 2]：[攻击前] → [攻击后]
```

**编写要求**：
- 至少包含 2 个独立的可观测差异点
- 攻击前后使用相同命令检测，便于对比
- 每个命令标注执行上下文层级
- 差分不依赖攻击者自身行为的变化

### 第 5 段：绕过策略

```markdown
## 5. 绕过策略

如果直接攻击被阻断（AppArmor/Seccomp/网络策略），可能的绕过方式。
每步标注执行上下文。没有则写"无已知绕过策略"。

### 阻断场景 1：[阻断机制名称]
- 检测命令：`[L1] command` → 期望输出：[侦测阻断机制]
- 绕过方式：[描述]
- [L2] `bypass_command` → 期望输出：[绕过成功指标]

### 阻断场景 N：[阻断机制名称]
- 检测命令：`[L1] command`
- 绕过方式：[描述]
```

**编写要求**：
- 按阻断机制分类（AppArmor、Seccomp、NetworkPolicy 等）
- 每种绕过方式提供可执行的检测和验证命令
- 无已知绕过策略时如实标注
- 遵守安全红线：绕过策略仅做理论分析，不实际执行破坏性绕过

### 第 6 段：证伪条件

```markdown
## 6. 证伪条件

什么条件下可以判定此攻击模式不适用，每步标注执行上下文（L0/L1）。

### 证伪条件
1. [L1] `command` → 输出 [X] → 证伪（前置条件不满足）
2. [L0] `command` → 输出 [Y] → 证伪（环境配置阻断）
3. [L1] `command` → 输出 [Z] → 证伪（安全机制阻断）

### 证伪判定规则
- 任意一条证伪条件满足 → 标记为 `[-]` 已证伪
- 证伪必须附证据：哪条命令的输出证明不可利用/被阻断
```

**编写要求**：
- 证伪条件必须具体、可执行
- 每条证伪条件标注执行上下文层级
- 证伪结果写入驻 `[ - ]` 标记和证伪依据

### 第 7 段：审批级别

```markdown
## 7. 审批级别

- L1：[只读探测类操作] → 自动审批
- L2：[容器内攻击验证] → standard approval
- L3：[破坏性操作] → manual approval（如适用）
```

**编写要求**：
- 列出该模式各步骤对应的审批级别
- L1 只读探测自动审批，L2 标准 approval，L3 手动 approval
- 破坏性操作标注为 L3 条件验证，不实际执行

### 第 8 段：MITRE ATT&CK

```markdown
## 8. MITRE ATT&CK

- [Technique ID] - [Technique Name]
- [Technique ID] - [Technique Name]
```

**编写要求**：
- 列出该攻击模式对应的 MITRE ATT&CK 技术编号和名称
- 每行一个技术，格式：`TXXXX - Technique Name`
- 与实际模式文件保持一致

---

## 3. 完整模板示例

以下是一个晋升为新攻击模式时使用的完整 SKILL.md 示例：

```markdown
---
source: learned
confidence: medium
platforms: [k8s, containerd]
mapped_attack_surfaces: [AS-1.7]
mapped_compliance_families: [Kubelet系统配置, 容器运行时安全]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
hit_count: 2
last_hit: 2026-06-20
promoted_date: 2026-06-20
created_from: insights.md#ATK-CAND-045
---

# containerd-shim 逃逸

## 1. 前置条件

### 环境要求
- 目标平台：containerd
- 攻击者上下文：容器内
- 目标服务版本范围：containerd < 1.6.x 或 shim 版本存在已知漏洞

### 必要条件（全部满足才可触发）
1. 容器运行时为 containerd（而非 Docker） → 检测命令：`[L0] crictl version`
2. containerd-shim socket 可访问 → 检测命令：`[L1] ls /run/containerd/io.containerd.runtime.v2.task/`
3. 当前容器有足够权限访问 shim API → 检测命令：`[L1] cat /proc/self/status | grep Cap`

### 增强（非必要但影响成功率）
1. 容器以特权模式运行 → 检测命令：`[L0] kubectl get pod xxx -o jsonpath='{.spec.securityContext.privileged}'`
2. Capabilities 包含 SYS_PTRACE → 检测命令：`[L1] capsh --print | grep SYS_PTRACE`

## 2. 探测命令

### 步骤 1：确认运行时类型
- [L0] `ssh_execute(server, "crictl version")` → 期望输出：containerd 版本信息
- [L1] `ssh_execute(server, "kubectl exec xxx -- ls /run/containerd/")` → 期望输出：containerd 运行时目录存在

### 步骤 2：确认 shim 可访问
- [L1] `ssh_execute(server, "kubectl exec xxx -- ls /run/containerd/io.containerd.runtime.v2.task/")` → 期望输出：shim socket 文件存在
- [L1] `ssh_execute(server, "kubectl exec xxx -- cat /proc/self/status | grep Cap")` → 期望输出：Capabilities 包含所需权限

## 3. 攻击验证

### 验证步骤
- [L2] `ssh_execute(server, "kubectl exec xxx -- {验证命令}")` → 期望输出：[攻击成功指标]
- [L2] `ssh_execute(server, "kubectl exec xxx -- {验证命令}")` → 期望输出：[攻击成功指标]
- [L2] `ssh_execute(server, "kubectl exec xxx -- {清理命令}")` → 清理临时资源

### 破坏性操作标注
- 本模式不包含破坏性操作

## 4. 差分证明

### 攻击前状态
- [L0] `docker ps` → 输出：无异常容器
- [L1] `cat /etc/shadow` → 输出：无法读取宿主机 shadow 文件

### 攻击后状态
- [L0] `docker ps` → 输出：出现新异常容器（或宿主机文件可访问）
- [L1] `cat /etc/shadow` → 输出：可读取宿主机 shadow 文件内容

### 差分总结
1. 容器列表变化：攻击前无异常容器 → 攻击后出现 shim 创建的异常容器
2. 文件访问变化：攻击前无法读取宿主机文件 → 攻击后可访问宿主机敏感文件

## 5. 绕过策略

### 阻断场景 1：AppArmor 限制 shim socket 访问
- 检测命令：`[L1] cat /proc/self/attr/current` → 期望输出：AppArmor profile 名称
- 绕过方式：寻找不受 AppArmor 保护的进程或 capability
- 无通用绕过方式时标注"无已知绕过策略"

## 6. 证伪条件

1. [L1] `ls /run/containerd/io.containerd.runtime.v2.task/` → 输出目录不存在 → 证伪（shim socket 不可访问）
2. [L0] `crictl version` → 输出 non-containerd runtime → 证伪（运行时不是 containerd）
3. [L1] `cat /proc/self/attr/current` → 输出限制性 AppArmor profile → 证伪（安全机制阻断）

### 证伪判定规则
- 任意一条证伪条件满足 → 标记为 `[-]` 已证伪，附证伪依据

## 7. 审批级别

- L1：探测 shim socket 可访问性 → 自动审批
- L2：shim socket 访问验证 → standard approval
- L3：破坏性逃逸验证 → manual approval（条件验证，不实际执行）

## 8. MITRE ATT&CK

- T1611 - Escape to Host
```

---

## 4. 晋升后的操作清单

晋升新模式完成后，必须执行以下操作：

| # | 操作 | 目标位置 |
|---|------|---------|
| 1 | 写入 SKILL.md | `attack-patterns/{攻击面}/_learned/{slug}/SKILL.md` |
| 2 | 更新 _index.md | 添加新模式条目，更新 hit_count 和 last_hit |
| 3 | 更新 _learned_index.md | 在 learned 模式索引中添加条目 |
| 4 | 更新 attack-hypotheses.md | 添加新模式的假设卡片（假设ID、攻击面引用、前置条件） |
| 5 | 更新 cross-ref-queries.md | 添加新模式对应的交叉关联查询 |
| 6 | 更新 VULNERABILITY_GROUPING.md | 在对应攻击面表格中添加新模式行 |
| 7 | 一致性检查 | LLM 语义检查三库一致性，输出不一致项 |

### _index.md 更新条目示例

```markdown
### containerd-shim-escape

- **文件**：escape/_learned/containerd-shim-escape/SKILL.md
- **来源**：learned（LLM 推理晋升，2026-06-20）
- **置信度**：medium
- **平台**：containerd
- **攻击面**：AS-1.7
- **命中次数**：2
- **最后命中**：2026-06-20
- **触发条件**：crictl version 显示 containerd + 容器内可见 shim socket
```