# 合规与安全红线

本文档定义容器渗透测试过程中的安全红线和合规规则编写规范。

---

## 1. 安全红线

以下红线在任何情况下都不可违反。违反红线将立即终止渗透测试会话。

### 红线 1：禁止利用漏洞造成实际损害

- 不准对生产系统执行破坏性操作（如删除数据、修改配置、停止服务）
- DoS 类攻击只做条件验证（L3），不实际执行 fork bomb、资源耗尽等攻击
- 所有 POC 脚本必须包含清理/恢复步骤
- 逃逸验证后必须立即清理（删除临时容器、恢复挂载等）

**越线判定**：任何导致服务中断、数据丢失、配置不可逆修改的操作。

### 红线 2：禁止持久化后门

- 不准在目标环境中植入后门（Webhook 后门、CronJob 持久化、SSH 密钥注入等）
- 持久化攻击模式只做条件验证（L3）：证明前置条件满足即可，不实际建立持久通道
- POC 中不得包含持久化步骤
- 任何创建长期资源的操作必须在验证后立即清理

**越线判定**：在目标环境中留下任何未清理的持久化机制。

### 红线 3：禁止向外泄露数据

- 不准将生产数据（Secret、凭证、用户数据）传输到测试人员环境之外
- 测试过程中读取的密钥/令牌只用于验证漏洞存在性，不用于实际访问其他系统
- Secret 验证只确认"可读取"，不确认"内容完整外泄"
- 报告中的密钥内容必须脱敏（只显示前 4 位 + 后 4 位，中间用 `***` 替代）

**越线判定**：将生产环境数据拷贝到非授权位置，或使用读取的凭证访问非测试范围系统。

### 红线 4：禁止影响生产可用性

- 所有攻击验证命令必须标注执行上下文层级（L0/L1/L2/L3）
- L3（条件验证）级别操作不实际执行，只做理论分析
- 高影响操作（Level 5 审批）需要显式用户确认
- SSH 命令限速：最大并行 3 条、批次间隔 2 秒、单次超时 30 秒
- kubectl exec 攻击验证后立即清理临时资源

**越线判定**：攻击验证导致服务降级或中断，且未在 5 分钟内恢复。

---

## 2. 合规规则编写规范

每条合规规则按照 CIS Benchmark 分组，使用以下统一格式：

### 2.1 规则格式

```markdown
### [规则编号] [规则标题]

- **描述**：[简要描述安全要求]
- **检查命令**：[用于检测的 SSH 命令，标注执行上下文层级]
- **判定标准**：
  - PASS：[通过条件]
  - FAIL：[失败条件]
  - WARN：[警告条件]
  - NA：[不适用条件]
- **修复建议**：[如何修复此问题]
- **CIS 原始引用**：[CIS Benchmark 编号]
```

### 2.2 格式字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| 编号 | 是 | 格式：`{平台}-{组号}.{规则号}`，如 `K8s-5.2.1`、`Docker-2.14`、`Containerd-3.1` |
| 描述 | 是 | 简要描述安全要求和风险，1-3 句话 |
| 检查命令 | 是 | 用于检测的 SSH 命令，每条命令标注执行上下文层级（L0/L1/L2/L3） |
| 判定标准 | 是 | 必须包含 PASS/FAIL/WARN/NA 四种情况的判定条件 |
| 修复建议 | 是 | 具体的修复命令或配置修改步骤 |
| CIS 原始引用 | 是 | CIS Benchmark 原始规则编号和标题 |

### 2.3 编号规范

| 平台 | 前缀 | 示例 |
|------|------|------|
| Kubernetes | `K8s-` | `K8s-5.2.1` |
| Docker | `Docker-` | `Docker-2.14` |
| Containerd | `Containerd-` | `Containerd-3.1` |

### 2.4 判定标准编写要求

1. **PASS** 条件必须明确可量化的配置值（如 `permissions: 600`、`owner: root:root`）
2. **FAIL** 条件必须对应具体的安全违规（如 `permissions: 644 或更宽松`、`anonymous-auth: true`）
3. **WARN** 用于部分满足或需人工判断的情况（如 `etcd 启用了 TLS 但客户端证书未验证`）
4. **NA** 条件要明确适用范围（如 `该规则仅适用于 etcd 独立部署场景`）
5. **不准使用模糊描述**：如"等"、"..."、"+(数量后缀)"、"大致"、"约"

### 2.5 检查命令编写要求

1. 每条命令标注执行上下文层级：`[L0]`、`[L1]`、`[L2]`、`[L3]`
2. 优先使用原生命令（kubectl/docker/crictl/shell 内置命令）
3. 提供主机级和容器级两种检查方式（如适用于两者）
4. 命令必须可直接复制执行，不含占位符
5. 复杂检查提供多条命令，每条命令标注期望输出

### 2.6 修复建议编写要求

1. 提供具体的修复命令或 YAML 配置片段
2. 注明修复的风险（如"修改此配置需要重启服务"）
3. 对生产环境修复给出逐步操作指南
4. 涉及安全红线操作的，标注"请确认后执行"

### 2.7 规则示例

```markdown
### K8s-5.2.1 不使用特权容器

- **描述**：特权容器拥有宿主机所有 capabilities，可突破容器隔离边界。应对 Pod 设置 securityContext.privileged: false。
- **检查命令**：
  - [L0] `kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext.privileged}{"\n"}{end}'` → 期望输出：所有行第二列为 false 或空
  - [L0] `kubectl get pods -A -o json | jq '.items[] | select(.spec.securityContext.privileged==true) | .metadata.name'` → 期望输出：空列表
- **判定标准**：
  - PASS：所有 Pod 的 privileged 字段为 false 或未设置（默认 false）
  - FAIL：存在 Pod 的 privileged 字段为 true
  - WARN：存在 Pod 继承命名空间的 privileged 设置（需人工确认）
  - NA：不适用
- **修复建议**：
  ```yaml
  apiVersion: v1
  kind: Pod
  spec:
    securityContext:
      privileged: false
  ```
  温馨提示：修改运行中 Pod 的 securityContext 需要重建 Pod，请在维护窗口期执行。
- **CIS 原始引用**：CIS Kubernetes Benchmark v1.8.0 - 5.2.1 "Minimize the admission of privileged containers"
```

### 2.8 分组与索引规范

每个平台的合规规则按 CIS Benchmark 分组存放，每组一个 MD 文件：

| 目录 | 内容 | 索引文件 |
|------|------|---------|
| `compliance-rules/kubernetes/` | K8s 134 条规则，按 CIS 分组（28 个文件） | `_index.md` |
| `compliance-rules/docker/` | Docker 64 条规则，按 CIS 分组（7 个文件） | `_index.md` |
| `compliance-rules/containerd/` | Containerd 28 条规则，按 CIS 分组（5 个文件） | `_index.md` |

每个目录的 `_index.md` 包含：

```markdown
# Kubernetes CIS Benchmark 规则索引

| 编号 | 标题 | 分组文件 | 规则数 |
|------|------|---------|--------|
| K8s-1.1.* | API Server 文件权限 | G_1_1_api_server_files.md | 7 |
| K8s-1.2.* | API Server 认证 | G_1_2_api_server_auth.md | 23 |
| ... | ... | ... | ... |

总计：134 条规则
```