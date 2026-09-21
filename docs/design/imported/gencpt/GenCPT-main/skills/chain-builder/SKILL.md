---
name: chain-builder
description: >
  攻击链构建。将多个已确认的攻击点组合成多步攻击链，评估可达性和影响。
  使用场景：Phase 4 发现多个可利用的攻击点。
  不使用场景：Phase 4 只发现零散攻击点、无法形成链。
---

## §0 套件根定位（启动第一步，强制）

本 SKILL 中所有相对路径（`skills/shared/`、`attack-patterns/`、`compliance-rules/`、`hypothesis-libraries/`、`references/`）均**相对套件根**，不相对 cwd。

**错误示例**（实际发生过）：SKILL 写 `skills/shared/SSH_COMMANDS.md`，LLM 拿 cwd `~/.config/opencode/skills/` 拼接 → 解析为 `~/.config/opencode/skills/shared/SSH_COMMANDS.md`（丢失套件根段 `gencpt/`）→ Read 失败。正确应为 `~/.config/opencode/skills/gencpt/skills/shared/SSH_COMMANDS.md`。

**若入口已传入套件根绝对路径**：直接用作前缀拼接所有相对路径，**不重复 Glob**。

**若未传入套件根**：用 Glob 工具定位，按以下顺序尝试首个命中：
- Pattern 1: `**/skills/shared/SSH_COMMANDS.md` → 套件根 = 命中路径向上两级
- Pattern 2: `**/gencpt/SKILL.md` → 套件根 = 命中路径父目录
- Pattern 3: `**/GenCPT*/SKILL.md` → 套件根 = 命中路径父目录

所有 Read 调用拼接套件根前缀：`skills/shared/X.md` → Read `{套件根}/skills/shared/X.md`。**禁用 `$ROOT/...` 变量形式**，Read 工具不展开 shell 变量。**不许凭记忆猜套件根路径**。

---

# chain-builder — Phase 5 攻击链构建

## MUST 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| knowledge_graph/edges/attack.json | Phase 4a/4b | 攻击边，包含 ATK-CAND 编号、status、verification_level、execution_context_max |
| knowledge_graph/edges/cross_ref.json | Phase 3 | 交叉关联边，包含合规违规→攻击前置条件的映射 |
| knowledge_graph/nodes/findings.json | Phase 2/4 | 发现节点，合规违规和攻击命中 |
| knowledge_graph/nodes/（其他节点） | Phase 1a | hosts/pods/containers/service_accounts/secrets 节点 |
| knowledge_graph/edges/infra.json | Phase 1a | 基础设施边，mount/capability/network 关系 |

## MUST 输出

| 输出 | 说明 |
|------|------|
| evidence/chains/chain_builder.md | 每条链的描述、步骤、影响评估、置信度 |
| knowledge_graph/edges/cross_ref.json | 追加 attack_chain 边到已有交叉关联文件 |

## 核心工作流

### 步骤 1：识别链起点

从 `knowledge_graph/edges/attack.json` 中查找 status 为 `confirmed` 或 `condition_met` 的 ATK-CAND 作为链起点。

**筛选规则**：
- 只取 status 为 `confirmed` 或 `condition_met` 的攻击边
- 排除 status 为 `high_risk_clue`（前置条件不完全满足，无法作为链起点）
- 排除 status 为不可利用或证伪的攻击边
- 按 `severity` 降序排列，优先处理 Critical 级别

**读取方式**：
1. 先 Read `knowledge_graph/edges/_index.md` 定位 attack.json 的范围
2. Read `knowledge_graph/edges/attack.json` 获取完整攻击边数据
3. 过滤出 confirmed/condition_met 的 ATK-CAND

**输出到 chain_builder.md**：

```markdown
## 链起点识别

| ATK-CAND | 攻击模式 | 来源 | 验证等级 | 执行上下文 | 目标 |
|----------|---------|------|---------|-----------|------|
| ATK-CAND-001 | socket-escape | pattern_library | C1 | L2 | pod-backend-api |
| ATK-CAND-003 | k8s-sa-exploit | llm_reasoning | C2 | L1 | pod-backend-api |
```

### 步骤 2：在知识图谱中查找可达攻击点

从每个链起点出发，通过 `cross_ref.json` 的边和 `attack` 边查找可达的下一个攻击点。

**查找策略**：

1. **读交叉关联边**：Read `knowledge_graph/edges/cross_ref.json`，获取所有 edge_type 为 `cross_ref` 的边
2. **读基础设施边**：Read `knowledge_graph/edges/infra.json`，获取网络、挂载、能力等关系边
3. **读发现节点**：Read `knowledge_graph/nodes/findings.json`，获取合规违规和攻击发现

**可达性判定**（按优先级）：

| 可达路径 | 条件 | 示例 |
|---------|------|------|
| 同目标级联 | 起点攻击成功后的后果直接满足下一攻击的前置条件 | 逃逸→宿主机访问→密钥窃取 |
| 跨目标传递 | 起点目标的网络可达下一目标，且下一目标存在可利用漏洞 | 容器A SA高权限→可访问容器B命名空间 |
| 权限提升链 | 低权漏洞→获得更高权限→触发需要高权限的漏洞 | 普通用户SA→RBAC提权→cluster-admin |
| 信息泄露→利用 | 泄露的凭证/Secret满足下一攻击的前置条件 | Secret读取→获得数据库密码→横向移动 |

**具体查找流程**：

```
对于每个链起点 ATK-CAND-X：
  1. 查找该 ATK-CAND 的 from_node（攻击目标：pod/容器/host）
  2. 查找以该目标为 from_node 的所有 infra 边（网络、挂载、capability）
  3. 通过 infra 边的 to_node 找到可达的新目标
  4. 检查新目标是否存在 confirmed/condition_met 的 ATK-CAND
  5. 同时检查起点的攻击后果是否满足下一 ATK-CAND 的前置条件
  6. 构建可达图：节点=ATK-CAND，边=可达路径+理由
```

**输出到 chain_builder.md**：

```markdown
## 可达性分析

### ATK-CAND-001 (socket-escape) 可达路径

| 下一步 ATK-CAND | 可达类型 | 可达理由 | 基础设施边 |
|----------------|---------|---------|-----------|
| ATK-CAND-005 (secret-exfil) | 同目标级联 | 逃逸后可访问宿主机 etcd 数据 | infra: pod→host mount |
| ATK-CAND-007 (lateral-move) | 跨目标传递 | 逃逸后可访问同节点其他 Pod 网络 | infra: pod→network |
```

### 步骤 3：判断链条可行性

检查每条链的每一步，前置条件是否被前一步满足。

**可行性判定规则**：

1. **严格前置条件检查**：链的第 N 步的前置条件必须被第 N-1 步的攻击后果满足，或被环境固有条件满足
2. **环境固有条件**：合规违规和基础设施边提供的固有条件，不依赖链前一步
3. **攻击后果满足**：前一步攻击成功后产生的新条件

**每条链的可行性检查**：

```
对于候选链 [ATK-CAND-A → ATK-CAND-B → ATK-CAND-C]：

第 1 步（ATK-CAND-A）：
  前置条件来源：环境固有条件（合规违规 + 基础设施）
  判定：✅/❌

第 2 步（ATK-CAND-B）：
  前置条件来源：
    - 环境固有条件（合规违规 + 基础设施）
    - ATK-CAND-A 的攻击后果（逃逸/提权/信息泄露）
  判定：✅ 全部满足 / ⚠️ 部分满足 / ❌ 不满足

第 3 步（ATK-CAND-C）：
  前置条件来源：
    - 环境固有条件
    - ATK-CAND-A 的攻击后果
    - ATK-CAND-B 的攻击后果
  判定：✅/⚠️/❌
```

**可行性等级**：

| 可行性 | 条件 | 标记 |
|--------|------|------|
| 可行 | 所有步骤前置条件全部满足 | ✅ |
| 条件可行 | 部分步骤前置条件依赖理论推导（C2/C3） | ⚠️ |
| 不可行 | 某步前置条件不满足且无法推导 | ❌ |

**输出到 chain_builder.md**：

```markdown
## 可行性分析

### CHAIN-001: socket-escape → secret-exfil → lateral-move

| 步骤 | ATK-CAND | 前置条件 | 来源 | 满足状态 |
|------|----------|---------|------|---------|
| 1 | ATK-CAND-001 (socket-escape) | 容器内有 docker.sock 且可读写 | 环境固有 (K8s-5.2.3 fail) | ✅ 满足 |
| 2 | ATK-CAND-005 (secret-exfil) | 宿主机访问 + etcd 可达 | ATK-CAND-001 后果 (宿主机访问) | ✅ 满足 |
| 3 | ATK-CAND-007 (lateral-move) | 可访问其他 Pod 网络 + 窃取的 SA Token | ATK-CAND-005 后果 (SA Token) | ⚠️ 部分满足 |

链条可行性: ⚠️ 条件可行（第3步依赖第2步窃取的 SA Token，若 etcd 网络不可达则断裂）
```

### 步骤 4：评估影响 + 分配置信度 + 编号

#### 4.1 链影响评估

每条链评估组合影响，按三个维度：

| 影响维度 | 评估标准 | 标记 |
|---------|---------|------|
| 逃逸深度 | 容器→宿主机→集群→云平台 | Escape-D1/2/3/4 |
| 提权范围 | 低权限→root→cluster-admin→云管理员 | Privesc-D1/2/3/4 |
| 持久化能力 | 无持久化→临时→重启存活→跨节点 | Persist-D1/2/3/4 |

深度定义：
- D1：单容器内提权/影响
- D2：同一节点范围内
- D3：集群范围内
- D4：跨集群/云平台级别

**组合影响评估公式**：

```
链影响 = max(逃逸深度) + max(提权范围) + 持久化能力权重

Critical:    逃逸D3+ 或 提权D3+ 或 持久化D3+
High:         逃逸D2+ 或 提权D2+ 或 持久化D2+
Medium:       逃逸D1+ 或 提权D1+ 或 持久化D1+
Low:          无逃逸且无提权
```

#### 4.2 置信度分配

基于链中每一步的验证等级确定链的置信度：

| 链中各步验证等级 | 链置信度 | 说明 |
|----------------|---------|------|
| 全部 C1（实证复现） | C1 | 链中每步都有 L2 差分证明 |
| 全部 C1/C2，至少一步 C2 | C2 | 条件成立步骤存在 |
| 包含 C3（风险线索） | C3 | 链中有前置条件不完全满足的步骤 |

**降级规则**：
- 链中任何一步为 C3 → 整条链降级为 C3
- 链中任何一步前置条件依赖理论推导（非实际验证）→ 降级为 C2
- 链中所有步骤 C1 且所有前置条件被实际验证满足 → C1

#### 4.3 链编号

格式：`CHAIN-001`, `CHAIN-002`, ...

**编号规则**：
- 按影响严重性降序编号（Critical 链优先编号）
- 同一严重级别内按置信度降序（C1 → C2 → C3）
- 编号连续无遗漏
- 每条链的每步必须有对应 ATK-CAND 编号

#### 4.4 写入知识图谱

将链信息追加到 `knowledge_graph/edges/cross_ref.json`，边格式：

```json
{
  "edge_type": "attack_chain",
  "chain_id": "CHAIN-001",
  "steps": [
    {
      "step": 1,
      "atk_cand_id": "ATK-CAND-001",
      "attack_name": "socket-escape",
      "source": "pattern_library",
      "status": "confirmed",
      "verification_level": "C1"
    },
    {
      "step": 2,
      "atk_cand_id": "ATK-CAND-005",
      "attack_name": "secret-exfil",
      "source": "pattern_library",
      "status": "confirmed",
      "verification_level": "C1"
    }
  ],
  "impact": {
    "escape_depth": "D2",
    "privesc_depth": "D3",
    "persist_depth": "D2",
    "severity": "Critical"
  },
  "feasibility": "conditional_feasible",
  "confidence": "C2",
  "description": "从业务容器出发，经Docker套接字逃逸至宿主机，利用etcd访问窃取集群Secret，通过窃取的SA Token横向移动至其他命名空间"
}
```

**写入规则**：
- 读取已有的 cross_ref.json
- 追加 attack_chain 类型的边
- 写回 cross_ref.json
- 更新 _index.md

## 检查点

完成前必须逐项确认：

- [ ] **① 每条链的每步前置条件被前一步满足**：链中没有任何一步的前置条件悬空（不被前一步或环境固有条件满足）
- [ ] **② CHAIN 编号连续无遗漏**：CHAIN-001 → CHAIN-002 → ...，无跳号
- [ ] **③ QA 结构校验通过**：
  - chain_builder.md 非空
  - 每条链有 chain_id、steps、impact、feasibility、confidence
  - 每条链的每步有对应 ATK-CAND 且在 attack.json 中存在
  - cross_ref.json 中 attack_chain 边的 from_node/to_node 能在 nodes 中找到对应节点
  - 无 `[ ]` 未检查标记残留

## 反幻觉硬约束

1. **不准凭记忆构建攻击链** — 每条链的每一步必须从 attack.json 和 cross_ref.json 中查到对应 ATK-CAND
2. **不准伪造可达关系** — 可达性必须基于 infra 边或 cross_ref 边的实际数据
3. **无证据不写确认态** — 只能基于已验证的 ATK-CAND（confirmed/condition_met）构建链
4. **前置条件不满足不强行链接** — 如果某步前置条件无法被满足，标记为 ⚠️ 不可强行编入
5. **省略词零容忍** — 不使用"等"、"..."、"+N"等省略表述
6. **占位符必须替换** — 所有【xxx】占位符必须替换为实际值

## 去重规则

- 链去重 key：steps 数组中所有 ATK-CAND ID 的有序拼接
- 相同去重 key → 保留置信度更高或影响更严重的链
- 不同链覆盖相同攻击路径时保留影响评估更详细的描述

## 上下文控制

- 上下文预算 ≤100k tokens
- 先读 _index.md 定位必要数据，只读当前分析需要的文件
- 分析结果立即写盘，释放上下文
- 返回 supervisory-agent 的摘要 ≤500 tokens

## 独立运行参数

```
--server prod-k8s-01 --session-dir /path/to/session
```
