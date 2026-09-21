# k8s-compliance 证据格式与写盘规则

> 本文件为 `skills/k8s-compliance/SKILL.md` 步骤 2-4 的证据格式和写盘规则参考。核心工作流见 SKILL.md。

---

## 五元组标注格式

每条命令的五元组标注写入 `evidence/compliance/k8s/raw/` 对应文件：

```
> 命令：<原始命令>
> 来源：<server> / <host_ip>
> 上下文：<L0 或 L1>
> 时间：<ISO 8601 时间戳>
> 退出码：<exit_code>
输出：<原始SSH输出，禁止删改>
```

---

## JSON Lines 写盘规则（防并发 + 防丢数据）

1. **JSON Lines 追加模式**：每条规则检测完成后立即追加写入 `evidence/compliance/k8s/results.jsonl`（每行一条 JSON），禁止累积满批再写：
   ```bash
   echo '{"rule_id":"K8s-1.1.1","verdict":"pass","evidence":"stat -c %a ...","host":"prod-k8s-01","ts":"2026-06-20T10:15:30Z"}' >> evidence/compliance/k8s/results.jsonl
   ```
2. **WU 完成时转为 JSON 数组**：
   ```bash
   jq -s '.' evidence/compliance/k8s/results.jsonl > evidence/compliance/k8s/results.json
   ```
3. **平台分片**：findings 写入 `findings_k8s.json`，compliance 边写入 `compliance_k8s.json`（不与其他平台共享文件）
4. **崩溃恢复**：WU 崩溃后从 `results.jsonl` 已有行数继续，不重做已检测的规则；恢复时先 `wc -l results.jsonl` 确定已完成的规则数，跳过对应的规则文件继续执行

---

## results.json 格式

```json
[
  {
    "rule_id": "K8s-1.1.1",
    "group": "G_1_1",
    "title": "API Server pod specification 文件权限",
    "status": "fail",
    "mark": "[x]",
    "evidence": {
      "command": "stat -c '%a' /etc/kubernetes/manifests/kube-apiserver.yaml",
      "output": "644",
      "context": "L0",
      "host": "prod-k8s-01 / 10.0.1.5",
      "timestamp": "2026-06-20T10:15:30Z",
      "exit_code": 0
    },
    "judgment": "文件权限 644 宽松于期望值 600，任何用户可读 API Server 配置",
    "cis_mapping": "CIS Kubernetes Benchmark v1.8.0 - 1.1.1",
    "attack_surface": "AS-2 认证授权",
    "remediation": "chmod 600 /etc/kubernetes/manifests/kube-apiserver.yaml"
  }
]
```

---

## summary.md 格式

```markdown
# K8s 合规检测摘要

## 统计

| 指标 | 数量 |
|------|------|
| 总规则数 | 134 |
| pass [-] | X |
| fail [x] | X |
| warn [!] | X |
| na [ ] | X |
| 可疑发现 [?] | X |
| 覆盖率 | X% |

## Critical 级别 fail 列表

| 规则 ID | 标题 | 判定理由 |
|---------|------|---------|
| K8s-x.x.x | ... | ... |

## 违规到攻击面映射

| 规则 ID | 攻击面 | 严重等级 |
|---------|--------|---------|
| K8s-x.x.x | AS-x | Critical |
```

---

## findings_k8s.json 格式（K8s 平台分片）

> **禁止**与其他平台（docker/containerd）共享文件。Phase 2 全部完成后由 Pipeline 入口汇总为 `findings.json`（见 OUTPUT_STANDARD §7 并发写入保护协议）。

```json
[
  {
    "id": "finding-k8s-1-1-1",
    "node_type": "finding",
    "data": {
      "rule_id": "K8s-1.1.1",
      "platform": "k8s",
      "status": "fail",
      "severity": "high",
      "title": "API Server pod specification 文件权限过于宽松",
      "judgment": "文件权限 644 宽松于期望值 600",
      "host": "prod-k8s-01"
    },
    "session_id": "sess-20260619-001"
  }
]
```

---

## compliance_k8s.json 格式（K8s 平台分片）

> **禁止**与其他平台共享文件。Phase 2 全部完成后由 Pipeline 入口汇总为 `compliance.json`。

```json
[
  {
    "edge_type": "compliance",
    "from_node": "host-prod-k8s-01",
    "to_node": "finding-k8s-1-1-1",
    "attrs": {
      "rule_id": "K8s-1.1.1",
      "status": "fail",
      "evidence": "stat -c '%a' /etc/kubernetes/manifests/kube-apiserver.yaml → 644",
      "platform": "k8s"
    }
  }
]
```

---

## finding evidence 字段（步骤 5c）

每个 finding 节点的 `data.evidence` 字段**必须非空**：

```json
{
  "id": "finding-k8s-1-1-1",
  "node_type": "finding",
  "data": {
    "rule_id": "K8s-1.1.1",
    "platform": "k8s",
    "status": "fail",
    "severity": "high",
    "title": "API Server pod specification 文件权限过于宽松",
    "judgment": "文件权限 644 宽松于期望值 600",
    "host": "prod-k8s-01",
    "evidence": {
      "command": "stat -c '%a' /etc/kubernetes/manifests/kube-apiserver.yaml",
      "output_summary": "644",
      "raw_ref": "evidence/compliance/k8s/raw/G_1_api_server.json",
      "context": "L0",
      "timestamp": "2026-06-20T10:15:30Z"
    }
  },
  "session_id": "sess-20260619-001"
}
```

**evidence 字段要求**：
- `command`：原始 SSH 命令
- `output_summary`：输出摘要（关键值）
- `raw_ref`：指向 `evidence/compliance/k8s/raw/` 下的原始输出文件路径
- `context`：执行上下文（L0/L1）
- `timestamp`：执行时间

**约束**：
- `data.evidence` 为空或缺失 → 该 finding 校验失败
- 此步骤修复"0/35 finding 有 evidence 字段"问题
