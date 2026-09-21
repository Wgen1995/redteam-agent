# GenCPT 知识图谱数据改进备忘

> 来源：2026-07-23 知识图谱可视化开发过程中发现的数据层面问题
> 涉及技能：`skills/attack-reasoning/SKILL.md`、`skills/attack-pattern/SKILL.md`、`skills/cross-ref/SKILL.md`、`skills/k8s-compliance/SKILL.md`、`skills/docker-compliance/SKILL.md`、`skills/containerd-compliance/SKILL.md`
> 状态：**已修复**（V1.2 第 3 组图谱层修复，2026-07-29）

---

## 问题 1：Phase 4b 改名导致 cross_ref 悬空引用

### 现象

`cross_ref.json` 中有一条边：

```json
{
  "edge_type": "cross_ref",
  "from_node": "compliance-K8s-1.2.20",
  "to_node": "attack-etcd-data-exposure",
  "reason": "K8s-1.2.20 fail: Secret未加密→ATK-HYP-047 etcd数据泄露",
  "attrs": { "query": "XREF-001", "severity": "critical" }
}
```

`attack.json` 中有两条边，但 `to_node` 是 `attack-kine-db-exposure`（改名后的）：

```json
{
  "edge_type": "attack_verify",
  "from_node": "host-k3s-server-192-168-139-66",
  "to_node": "attack-kine-db-exposure",
  "attrs": { "atk_cand": "ATK-CAND-022/041", "status": "confirmed", "confidence": "C1" }
}
{
  "edge_type": "attack_verify",
  "from_node": "host-k3s-server-192-168-139-66",
  "to_node": "attack-kine-db-exposure",
  "attrs": { "atk_cand": "ATK-CAND-045", "status": "confirmed_conditional", "confidence": "C2", "source": "llm_reasoning" }
}
```

### 根因

Phase 3 交叉关联时，根据攻击假设库创建了 `attack-etcd-data-exposure` 的假设边。

Phase 4b LLM 推理时，发现 k3s 使用的是 Kine SQLite 数据库而非 etcd，把攻击名从 `etcd-data-exposure` 改为 `kine-db-exposure`，在 `attack.json` 中追加了验证边。

但 Phase 4b **没有回写 `cross_ref.json`**，没有更新或追加 `compliance-K8s-1.2.20 → attack-kine-db-exposure` 的边。

### 影响

1. 知识图谱中 `attack-etcd-data-exposure` 有假设（cross_ref 边）但无验证（attack_verify 边），呈现为"未验证"状态
2. `attack-kine-db-exposure` 有验证但 cross_ref 不指向它，追溯链断裂：`合规规则 → ??? → 验证结果`
3. `coverage_report.md` 中 `etcd-data-exposure C1 confirmed` 和 `ATK-CAND-022/041` 的记录无法对应到知识图谱中的边
4. `attack_report.md` 中写的是 `📚 etcd-data-exposure + 🧠 kine-db-exposure`，说明报告层面已经知道是同一个攻击，但知识图谱边层面没有关联

### 修复状态：已修复

**修复方案**：在 `skills/attack-reasoning/SKILL.md` 步骤 3（生成 ATK-CAND）后增加步骤 3b"改名回写 cross_ref"：
- 检测 Phase 4b 验证的 attack_name 与 cross_ref.json 中假设边 to_node 不一致时识别为改名场景
- 在 `cross_ref.json` 追加新边：from_node=原合规规则, to_node=新 attack_name, attrs.renamed_from=原 attack_name
- 保留旧边作为历史记录
- 确保追溯链不断裂：`合规规则 → cross_ref(新) → attack(验证)`

**所在文件**：`skills/attack-reasoning/SKILL.md` 步骤 3b

---

## 问题 2：Phase 4a 无法验证的 attack 在知识图谱中无标记

### 现象

`cross_ref.json` 中有一条边：

```json
{
  "edge_type": "cross_ref",
  "from_node": "compliance-K8s-8.2.10",
  "to_node": "attack-cloud-metadata",
  "reason": "K8s-8.2.10 + 7.1.5 fail: 无NP+hostNetwork→ATK-HYP-009云元数据窃取",
  "attrs": { "query": "XREF-001", "severity": "high" }
}
```

`attack.json` 中**没有** `attack-cloud-metadata` 的 attack_verify 边。

`coverage_report.md` 中记录：
```
| AS-3 网络 | cloud-metadata | 环境限制 | Orbstack非云环境，169.254.169.254不可达 | 中 | 建议在云环境补充验证 |
```

### 根因

Phase 3 创建了 `attack-cloud-metadata` 的攻击假设。

Phase 4a 模式匹配时，由于环境限制（Orbstack 桌面虚拟化环境，非云平台，169.254.169.254 不可达），无法验证这个攻击。

Phase 4a **没有在知识图谱中记录"无法验证的原因"**——只是在 `coverage_report.md` 的未覆盖事项中记录了，但 `cross_ref.json` 和 `attack.json` 中没有任何标记。

### 影响

1. 知识图谱中 `attack-cloud-metadata` 有假设但无验证，无法区分"4a 漏了"和"环境限制无法验证"
2. 下游 Phase（如 Phase 5 链构建）无法判断这个 attack 是否可用
3. 可视化中只能标记为"未验证"，无法显示原因

### 修复状态：已修复

**修复方案**：在 `skills/attack-pattern/SKILL.md` 步骤 3（处理未匹配信号）后增加步骤 3b"无法验证的 attack 标记 unverified 边"：
- 无法验证的 attack 追加 `attack_verify` 边到 `attack.json`，status="unverified"
- `attrs.unverified_reason` 写明具体原因
- `attrs.unverified_category` 从 5 个类别中选取：environment_limitation / tool_missing / approval_blocked / condition_not_met / out_of_scope
- 原有 cross_ref 假设边保留
- 知识图谱中可区分"4a 漏了"和"环境限制无法验证"

**所在文件**：`skills/attack-pattern/SKILL.md` 步骤 3b

---

## 问题 3（次要）：Phase 2 compliance 边缺对象级关联

### 现象

`compliance_k8s.json` 中所有 34 条 compliance 边的 `from_node` 都是 `host-k3s-server`：

```json
{
  "edge_type": "compliance",
  "from_node": "host-k3s-server",
  "to_node": "finding-k8s-k8s-7-1-1",
  "attrs": { "rule_id": "K8s-7.1.1", "status": "fail", "evidence": "..." }
}
```

但 finding 的 `judgment` 字段中提到了具体违规对象：
```
"judgment": "4个特权容器: privileged-escape-target, docker-sock-escape, suspicious-daemonset*, cloud-metadata-access"
```

没有结构化的 `pod → finding` 边。

### 根因

Phase 2 合规检测在 host 上执行，检测结果（finding）记录在 host 级别。judgment 文本中提到了具体对象名，但没有创建从对象到 finding 的边。

### 影响

1. 知识图谱中无法从 Pod/Container 追溯到它违反了哪些合规规则
2. Phase 3 交叉关联只能从 `compliance-rule → attack-hypothesis`（XREF-001），不能从 `违规对象 → attack-hypothesis`
3. 可视化中需要从 judgment 文本匹配对象名来派生关联边

### 修复状态：已修复

**修复方案**：在 3 个合规 SKILL 的步骤 4（写入数据）中增加步骤 4b/5b（对象级 compliance 边）和步骤 4c/5c（finding evidence 字段）：
- **对象级边**：从 finding 的 judgment 字段提取违规对象名（Pod/Container/SA/Secret），对每个违规对象追加 `对象→finding` compliance 边，attrs.relation="violates"，原有 host→finding 边保留
- **evidence 字段**：每个 finding 节点的 data.evidence 必须非空，包含 command、output_summary、raw_ref、context、timestamp

**所在文件**：
- `skills/k8s-compliance/SKILL.md` 步骤 4.5（对象级边）+ 4.6（evidence 字段）
- `skills/docker-compliance/SKILL.md` 步骤 4b（对象级边）+ 4c（evidence 字段）
- `skills/containerd-compliance/SKILL.md` 步骤 4b（对象级边）+ 4c（evidence 字段）

---

## 可视化层面的兜底处理（已实现）

以上 3 个问题在可视化中已做兜底，不影响图的展示效果：

| 问题 | 可视化兜底方式 | GenCPT 修复后状态 |
|------|--------------|------------------|
| 问题1：改名悬空 | `attackNameAlias` 别名映射，将 `attack-etcd-data-exposure` 的边重定向到 `attack-kine-db-exposure` | GenCPT 已回写 cross_ref，可视化兜底仍保留作为兼容 |
| 问题2：未验证无标记 | 虚拟节点创建时 `status: 'unverified'`，灰色虚线边框显示 | GenCPT 已追加 unverified 边，可视化可直接读取 KG 中的 unverified 状态 |
| 问题3：缺对象级边 | `compliance_object` 派生边，用 `wordMatch` 从 judgment 文本匹配对象名 | GenCPT 已建对象级边，可视化兜底仍保留作为补充 |

**3 个问题已全部修复**，GenCPT 知识图谱本身现已自洽。可视化层面的兜底处理保留作为兼容层，不影响功能。
