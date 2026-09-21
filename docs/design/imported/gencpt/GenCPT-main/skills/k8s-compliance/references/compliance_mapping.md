# k8s-compliance 合规假设映射规则

> 本文件为 `skills/k8s-compliance/SKILL.md` 步骤 3 完成后的合规假设映射参考。核心工作流见 SKILL.md。

---

## 合规假设映射（步骤 3 完成后执行）

完成 4 个 WU 的判定后，对每条 fail 规则执行合规假设映射：

1. 读取 `hypothesis-libraries/compliance-hypotheses.md`
2. 对每条 fail 规则，查找对应的攻击假设映射
3. 生成 `knowledge_graph/edges/compliance.json` 中的边，连接 `finding` 节点到攻击假设节点
4. 映射结果记录到 `results.json` 的 `attack_surface` 字段

---

## COMP-CAND 编号规则

- 合规违规候选（COMP-CAND）编号格式：`COMP-CAND-{序号}`
- 序号从 001 开始递增，按检测顺序分配
- 每个 COMP-CAND 关联一条或多条 fail 规则
- COMP-CAND 在 Phase 3（cross-ref）中与 ATK-CAND 交叉关联
- `attack_surface` 字段值格式：`AS-{编号} {攻击面名称}`（如 `AS-2 认证授权`）

---

## 违规到攻击面映射示例

| 规则 ID | 攻击面 | 严重等级 | 映射依据 |
|---------|--------|---------|---------|
| K8s-1.1.1 | AS-2 认证授权 | High | API Server 配置文件权限宽松，可被利用读取敏感配置 |
| K8s-7.1.1 | AS-1 逃逸 | Critical | 特权容器可逃逸至宿主机 |

映射结果写入 `results.json` 的 `attack_surface` 字段和 `knowledge_graph/edges/compliance_k8s.json`。
