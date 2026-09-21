---
name: graph-viz
description: >
  知识图谱可视化生成器（可选能力）。读取会话目录的 knowledge_graph/ 数据，
  生成交互式 HTML 可视化文件，支持在线/离线两种模式。
  使用场景：Phase 8c 完成后生成可视化报告，或任意时刻查看图谱。
  不使用场景：knowledge_graph/ 目录为空或不存在。
---

# Phase 8d — 知识图谱可视化生成（可选）

## §0 套件根定位

同入口 SKILL.md §0。本技能的参考文件位于 `{套件根}/skills/graph-viz/`。

## 定位

**可选能力**，不阻塞 Pipeline。Phase 8c 完成后自动调用，也可手动调用。

## 执行方式

### 方式一：直接运行 Python 脚本（推荐，100% 复现）

```bash
# 默认：V1.1 带星云旋转，离线模式（推荐，约 520KB，完全自包含）
python3 {套件根}/skills/graph-viz/generate_viz.py -s {session_dir} --offline

# V1.1 带旋转，在线模式（约 170KB，需联网）
python3 {套件根}/skills/graph-viz/generate_viz.py -s {session_dir}

# V1 不带旋转
python3 {套件根}/skills/graph-viz/generate_viz.py -s {session_dir} --no-rotate --offline

# 自定义输出路径和标题
python3 {套件根}/skills/graph-viz/generate_viz.py -s {session_dir} --offline -o {session_dir}/reports/viz.html -t "渗透测试报告"
```

> **推荐使用 `--offline` 离线模式**：cytoscape.js 内嵌在 HTML 中，不依赖网络，文件可发送给任何人。在线模式依赖 CDN，网络不通时页面白屏无内容。

### 版本说明

| 参数 | 模板 | 说明 |
|------|------|------|
| 默认 / `--rotate` | `template_v1.1.html` | V1.1 带星云旋转功能 |
| `--no-rotate` | `template.html` | V1 不带旋转 |

### 方式二：LLM 直接生成（当脚本不可用时）

当 Python 环境不可用或需要定制时，LLM 参考下面的规范和参考文件直接生成 HTML。

## 参考文件

| 文件 | 作用 |
|------|------|
| `skills/graph-viz/template.html` | V1 模板（无旋转）——完整的 CSS 样式、Cytoscape.js 图逻辑、交互功能 |
| `skills/graph-viz/template_v1.1.html` | V1.1 模板（带旋转）——在 V1 基础上加星云旋转功能 |
| `skills/graph-viz/generate_viz.py` | Python 生成脚本——读取 JSON、自动修复语法、合并数据、注入模板。默认用 V1.1 模板 |
| `skills/graph-viz/example_output.html` | V1 已验证示例输出 |
| `skills/graph-viz/example_output_v1.1.html` | V1.1 已验证示例输出 |

## 数据前提

**所有数据由 GenCPT skill 生成，格式固定。** 可视化的职责是忠实展示 GenCPT 知识图谱，不是处理未知格式。

GenCPT 知识图谱的固定数据结构：

| 文件 | 内容 | 格式 |
|------|------|------|
| `knowledge_graph/nodes/hosts.json` | 主机节点 | `[{id, node_type:"host", data:{hostname,ip,...}}]` |
| `knowledge_graph/nodes/pods.json` | Pod 节点 | `[{id, node_type:"pod", data:{namespace,name,security_context,...}}]` |
| `knowledge_graph/nodes/containers.json` | 容器节点 | `[{id, node_type:"container", data:{name,image,...}}]` |
| `knowledge_graph/nodes/services.json` | 服务节点 | `[{id, node_type:"service", data:{name,type,...}}]` |
| `knowledge_graph/nodes/service_accounts.json` | SA 节点 | `[{id, node_type:"service_account", data:{name,...}}]` |
| `knowledge_graph/nodes/secrets.json` | Secret 节点 | `[{id, node_type:"secret", data:{name,type}}]` |
| `knowledge_graph/nodes/findings.json` | 合规发现（汇总） | `[{id, node_type:"finding", data:{rule_id,severity,...}}]` |
| `knowledge_graph/nodes/findings_k8s.json` | K8s 合规发现（分片） | 同上，与 findings.json 有重复 |
| `knowledge_graph/nodes/findings_containerd.json` | Containerd 合规发现 | 同上 |
| `knowledge_graph/edges/infra.json` | 基础设施边 | `[{edge_type:"infra", from_node, to_node, attrs:{relation}}]` |
| `knowledge_graph/edges/compliance.json` | 合规边（汇总） | `[{edge_type:"compliance", from_node:"host-*", to_node:"finding-*"}]` |
| `knowledge_graph/edges/compliance_k8s.json` | K8s 合规边（分片） | 同上，与 compliance.json 有重复 |
| `knowledge_graph/edges/cross_ref.json` | 交叉关联+攻击链 | `[{edge_type:"cross_ref"/"attack_chain", ...}]` |
| `knowledge_graph/edges/attack.json` | 攻击验证边 | `[{edge_type:"attack_verify", from_node, to_node, attrs:{status,confidence,...}}]` |
| `knowledge_graph/edges/_derived.json` | 派生边（graph-viz 写回） | `[{edge_type, from_node, to_node, attrs:{derived:true, derived_by:"graph-viz",...}}]` |
| `progress.json` | Pipeline 状态 | `{phases:{"1a":{status,last_updated,...}}}` |
| `session_config.json` | 环境信息 | `{session_id, target, env_fingerprint,...}` |

**已知的数据特征（GenCPT 固有，不是 bug）：**
- `findings.json` 与 `findings_k8s.json` 内容重复 → 合并时按 ID 去重
- `compliance.json` 与 `compliance_k8s.json` 内容重复 → 合并时按 from+to+type 去重
- `attack_verify` 边的 `to_node`（如 `attack-socket-escape`）在 nodes 中不存在 → 派生虚拟节点
- `attack_chain` 边的 `to_node`（如 `CHAIN-001`）在 nodes 中不存在 → 派生虚拟节点
- `attack_chain` 的 `steps` 数组中有些 `attack_name` 没有 `attack_verify` 边 → 派生虚拟节点
- `cross_ref` 边引用 `compliance-*`/`target-*`/`amplification-*` 等不在 nodes 中的 ID → 派生虚拟节点
- compliance 边全部从 `host` 出发，没有关联到具体 Pod/Container → 从 judgment 文本派生 `对象→finding` 边
- Phase 1a 只为高风险 SA 建 `uses_sa` 边 → 从 Pod.serviceAccountName 补全
- Pending Pod 的 `node` 字段为 `pending` → 这是真实状态（未调度），不创建虚拟 host，不派生 runs_on 边

从 `{session_dir}/knowledge_graph/` 读取所有 JSON：

```
nodes/*.json → 合并为 nodes 数组
edges/*.json → 合并为 edges 数组
../progress.json → Pipeline 状态
../session_config.json → 环境信息
```

**JSON 自动修复**：数组元素之间缺少逗号（`}` 和 `{` 之间）时自动补逗号。修复时打印 WARN，不修改原始文件。

### 2. 虚拟节点派生（关键）

edges 中 `attack_verify` 和 `attack_chain` 边的 `to_node`（如 `attack-socket-escape`、`CHAIN-001`）在 nodes 中不存在。必须从边数据自动派生虚拟节点：

| 边类型 | 缺失端点 | 虚拟节点类型 | 从 ID 前缀判断 |
|--------|---------|-------------|---------------|
| attack_verify | to_node | attack | `attack-*` |
| attack_verify | from_node | attack | `rbac-*`、`secret-*`→secret |
| attack_chain | to_node | chain | `CHAIN-*` |
| attack_chain | from_node | host | `host-*`（含 IP） |
| cross_ref | 任意端点 | finding | `compliance-*` |
| cross_ref | 任意端点 | attack | `target-*`、`amplification-*` |
| cross_ref | 任意端点 | container/secret/SA/host | 按前缀匹配 |
| attack_chain steps | attack_name | attack | 只存在于 chain steps 中但无 attack_verify 边的（如 `kine-bootstrap-token`），从 steps 数组派生虚拟 attack 节点 |
| Pending Pod | 不派生 | `node=pending` 是真实状态（未调度），不创建虚拟 host |

**兜底规则**：无法判断类型时，默认创建 attack 节点。绝不能丢弃边。

**别名映射**：Phase 4b LLM 推理可能改变攻击名（如 `etcd-data-exposure` → `kine-db-exposure`），cross_ref 中保留原始假设名但 attack_verify 中用新名。必须在虚拟节点创建前建立别名映射（`attackNameAlias`），跳过有别名的不创建虚拟节点，在边过滤时将 to_node 重定向到新名。

### 2a. 派生边（从现有数据按 GenCPT 渐进式增强逻辑派生）

原始知识图谱数据存在关联缺失（GenCPT 各 Phase 只建精准备选边），可视化必须从现有数据派生完整关联：

| 派生边类型 | 来源 | 逻辑 | 对应 Phase |
|-----------|------|------|-----------|
| `uses_sa` | Pod.serviceAccountName + SA namespace/name | Phase 1a 只为高风险 SA 建 uses_sa，这里按 namespace+name 匹配补全所有 Pod→SA | Phase 1a 补全 |
| `compliance_object` | finding.judgment 文本匹配 | 解析 judgment 中提到的 pod/container/SA/secret 名称，建 `对象→finding` 边 | Phase 2 增强 |
| `finding_to_attack`（精确） | cross_ref 的 compliance-* → attack-* | 映射 compliance-rule 到 finding ID，建 `finding→attack` 边 | Phase 3 |
| `finding_to_attack`（模糊） | finding.attack_surface 字段 | 通过 attack_surface（AS-1~AS-5）映射到同攻击面的已验证 attack | Phase 4a/4b 覆盖 |
| `chain_step` | attack_chain 的 steps 数组 | 按步骤顺序建 `attack-step1 → attack-step2 → ...` 边 | Phase 5 |
| ~~`runs_on`（Pending）~~ | ~~Pending Pod~~ | ~~不派生~~ | Pending Pod 未调度是真实状态，不需要补 runs_on |

**attack_surface 映射表**（AS → attack 类型）：

```
AS-1 逃逸: privileged-container-escape, hostpath-mount-escape, capability-privesc, socket-escape, hostpid-hostipc-escape, hostnetwork-abuse
AS-2 认证: k8s-rbac-abuse, k8s-sa-exploit, k8s-anonymous-access, kubelet-api-abuse
AS-3 网络: lateral-move
AS-4 数据: secret-exfil, env-credential-leak, kine-db-exposure, configmap-data-exposure
AS-5 DoS:  resource-abuse
```

### 2b. 派生边持久化

派生边（§2a 中从现有数据按 GenCPT 渐进式增强逻辑派生的边）**必须写回 KG**，而非仅存在于可视化内存中：

**写入规则**：
- 派生边写入 `knowledge_graph/edges/_derived.json`（独立文件，不混入原始边文件）
- 每条派生边标注 `attrs.derived: true`
- 每条派生边标注 `attrs.derived_by: "graph-viz"`
- **原始边文件不被修改** — `infra.json`、`compliance.json`、`cross_ref.json`、`attack.json` 保持不变

**派生边文件格式**：

```json
[
  {
    "edge_type": "uses_sa",
    "from_node": "pod-default-frontend",
    "to_node": "sa-default-default",
    "attrs": {
      "relation": "uses_sa",
      "derived": true,
      "derived_by": "graph-viz",
      "derived_reason": "Phase 1a 未建 uses_sa 边，从 Pod.serviceAccountName 按 namespace+name 匹配补全"
    },
    "timestamp": "2026-07-23T12:00:00Z"
  },
  {
    "edge_type": "compliance_object",
    "from_node": "pod-vuln-apps-privileged-escape-target",
    "to_node": "finding-k8s-k8s-7-1-1",
    "attrs": {
      "rule_id": "K8s-7.1.1",
      "status": "fail",
      "relation": "violates",
      "derived": true,
      "derived_by": "graph-viz",
      "derived_reason": "从 finding.judgment 文本匹配 Pod 名称派生对象→finding 边"
    },
    "timestamp": "2026-07-23T12:00:00Z"
  }
]
```

**约束**：
- 派生边文件 `_derived.json` 是只追加文件，每次可视化生成时追加新派生边
- 同一 from_node + to_node + edge_type 的派生边去重（保留第一条）
- `_derived.json` 中的边在后续 Pipeline Phase 中可被读取，作为补全关联的参考
- 可视化读取时将 `_derived.json` 与原始边文件合并展示

### 2c. 数据去重（脚本层面）

`generate_viz.py` 合并 JSON 时必须去重：
- **节点去重**：同 ID 的节点只保留第一个（`findings.json` 和 `findings_k8s.json` 可能有重复）
- **边去重**：同 `from_node + to_node + edge_type + atk_cand` 的边只保留第一个。**注意：attack_verify 边可能有多条指向同一 attack（不同 ATK-CAND、不同 Phase 来源），不能只按 from+to+type 去重，必须加入 atk_cand 字段**

### 3. 技术栈

- **Cytoscape.js 3.30+**（CDN: `https://unpkg.com/cytoscape@3.30.2/dist/cytoscape.min.js`）
- 离线模式：下载 cytoscape.min.js 内嵌到 `<script>` 标签中
- 零其他依赖，纯前端 HTML 文件

### 4. 页面布局（从上到下）

1. **统计栏**：节点数 / 边数 / 合规违规数 / Critical 数 / 攻击链数 / 确认攻击数 / 综合评分（动态计算）/ 环境信息
2. **Pipeline 时间轴**：按显式顺序 `PHASE_ORDER` 数组排列（1a→1b→2a→2b→2c→3→4a→4b→5→6→7→8a→8b→8c→9），**不依赖 Object.keys 排序**
3. **工具栏**：节点类型过滤 / 边类型过滤 / Namespace 过滤 / Severity 过滤 / 搜索 / 布局切换 / 视图标签页（Cytoscape 图 / 思维导图）
4. **主图区**（flex:1 填满剩余高度）+ **右侧面板**（400px 宽）
5. **右侧面板内容**（从上到下）：
   - 节点/边详情面板
   - 可信度分布面板（C1/C2/C3/不可利用/已阻断 分布统计，饼图或条形图）
   - 覆盖率面板（7 攻击面 × 模式库覆盖/LLM推理覆盖/总覆盖，理论可 100% 覆盖的单元格标红）
   - 攻击链面板
6. **图例**：左下角浮动，可折叠

**思维导图视图**：工具栏中增加"思维导图"标签页，切换后主图区替换为树状结构：
- 根节点："渗透测试会话 {session_id}"
- 第一层：环境侦察 / 合规检测 / 交叉关联 / 攻击验证 / 攻击链 / POC / 报告
- 第二层：各 Phase 的具体产出（如环境侦察下展开 hosts/pods/containers 节点）
- 嵌套 HTML 列表实现，可折叠展开
- 节点可点击跳转回 Cytoscape 图中对应节点并高亮

### 5. 节点视觉编码

| 节点类型 | 形状 | 颜色 | 特殊标记 |
|---------|------|------|---------|
| host | round-rectangle | #4A5568 | — |
| pod | ellipse | 按 namespace 着色 | 特权 Pod 红色边框+发光 |
| container | rectangle | #B7791F | — |
| service | hexagon | #3182CE | — |
| service_account | triangle | #805AD5 | high-priv-app-sa 橙色边框 |
| secret | diamond | #E53E3E | app-db-credentials 红色边框 |
| finding | round-rectangle | 按 severity 着色 | Critical 红色发光+"!" |
| attack | vee | 按来源和状态着色（见下） | 按状态加图标 |
| chain | star | #2D3748 | 金色发光边框 |

**五态着色（Pod/Container 节点）**：按节点 security_context 的五态标记着色：
| 五态标记 | 颜色 | 含义 |
|---------|------|------|
| `[x]` | 红色 #f85149 | 已确认可利用 |
| `[?]` | 橙色 #d29922 | 疑似/待验证 |
| `[-]` | 绿色 #3fb950 | 已证伪/不可利用 |
| `[!]` | 黄色 #e3b341 | 已阻断（安全机制） |
| 无标记 | 按 namespace 默认着色 | 未检查 |

**Attack 来源与状态着色**（与 attack_report.md 一致）：

| 颜色 | 来源/状态 | 说明 |
|------|----------|------|
| #C53030 深红 | 📚 pattern_library | Phase 4a 模式库匹配 |
| #9B59B6 紫色 | 🧠 llm_reasoning | Phase 4b LLM 推理发现 |
| #E91E63 粉红 | 📚🧠 both | 模式库+LLM 两者（同一 attack 有两条 source 不同的 attack_verify 边） |
| #d29922 橙色 | ⚠️ risk_clue / high_risk_clue | C3 风险线索 |
| #6e7681 灰色 | 🛑 blocked | 已阻断 |
| #6e7681 灰色虚线边框 | ❓ unverified | cross_ref 假设但无 attack_verify（未验证） |

**source 判断逻辑**：收集所有指向同一 attack 的 attack_verify 边的 source 字段，无 source 字段视为 `pattern_library`。如果同时有 `pattern_library` 和 `llm_reasoning` → `both`。

**Namespace 着色**：已知 namespace 有固定颜色，未知 namespace 自动分配颜色（兜底池）。
**Severity 着色**：critical=#f85149 / high=#d29922 / medium=#e3b341 / low=#768390，未知用兜底色。
**未知节点类型**：自动分配颜色和默认形状（兜底池），不崩溃。

### 6. 边视觉编码

| 边类型 | 线型 | 颜色 | 说明 |
|-------|------|------|------|
| runs_on | 实线 | #718096 | 细线 |
| container_in | 实线 | #A0AEC0 | 细线 |
| exposes | 虚线 | #3182CE | 中线 |
| host_path_mount | 实线 | #E53E3E | 粗线，标签显示路径 |
| uses_sa | 实线 | #805AD5 | 中线 |
| compliance | 点线 | 按 status | 细线 |
| cross_ref | 虚线 | 按 severity | 中线 |
| attack_verify (confirmed) | 实线 | #C53030 | 粗线 |
| attack_verify (conditional) | 虚线 | #C53030 | 中线 |
| attack_verify (risk_clue) | 点线 | #d29922 | 细线 |
| attack_verify (blocked) | 点线 | #6e7681 | 细线 |
| attack_chain | 实线动画 | #D69E2E | 粗线，金色流动动画 |
| **未知边类型** | 实线 | #6e7681 | 兜底灰色 |

### 7. 交互功能

- **点击节点**：右侧面板显示属性（优先已知字段顺序，未知字段自动追加）+ 入出边列表（可点击跳转），入出边列表显示 XREF-001/002/003 标签和 reason
- **点击边**：右侧面板显示边详情（edge_type、relation、from/to、query、severity、status、confidence、atk_cand、level、source、chain_id、violation_count、reason 等），attack_chain 边额外显示步骤列表
- **悬停**：tooltip 显示摘要
- **双击 chain 节点**：高亮该链完整路径
- **双击攻击面节点（AS-1~AS-7）**：高亮完整追溯链（从合规规则→交叉关联→攻击验证→攻击链→POC）
- **点击攻击链面板中的链**：展开步骤 + 高亮图中路径
- **点击 Phase 时间轴**：高亮该 Phase 产出的节点和边，其余淡化；无数据的 Phase 显示提示信息
- **过滤工具栏**：节点类型/边类型/Namespace/Severity 复选框过滤 + 搜索 + 4 种布局切换 + 星云旋转控件
- **面板折叠**：点击"节点/边详情"或"攻击链"标题栏可折叠/展开，折叠后释放空间给另一面板
- **图例**：形状与实际渲染一致，可折叠
- **星云旋转（V1.1）**：工具栏中"星云旋转 OFF/ON"按钮 + 速度滑块（5-180秒/圈），旋转节点 position 不破坏交互
- **思维导图视图**：Cytoscape 图旁增加"思维导图"标签页，树状结构从"渗透测试会话"展开：环境侦察→合规检测→交叉关联→攻击验证→攻击链→POC→报告，嵌套 HTML 列表实现，可折叠展开，节点可点击跳转 Cytoscape 图节点

### 节点标签显示规范

- 标签截断长度：50 字符（超出用 `..` 表示）
- Cytoscape 样式：`text-wrap: wrap`，`text-max-width: 160px`（自动换行）
- attack 节点标签格式：`ATK-CAND-XXX 攻击名 C1 📚✅`（ATK-CAND ID + 攻击名 + 置信度 + 来源图标 + 状态图标）
- 来源图标：📚 模式库 / 🧠 LLM 推理 / 📚🧠 两者
- 状态图标：✅ confirmed / ⚡ conditional / ⚠️ risk / 🛑 blocked / ❓ unverified
- attack 节点详情中 source 字段显示具体的 XREF-001/002/003（从 cross_ref 边的 query 字段提取），不是笼统的 "cross_ref"

### 边标签显示规范

- cross_ref 边在图上显示 `XREF-001`/`XREF-002`/`XREF-003` 标签（从 attrs.query 提取）
- 节点详情中的入出边列表也显示 XREF 标签和 reason（截断到 50 字符）

### 8. 布局

- `html, body` 设 `height: 100%`
- `body` 用 `display: flex; flex-direction: column`
- 顶部三栏（统计/Pipeline/工具栏）`flex-shrink: 0`
- 主布局 `#main-layout` 用 `flex: 1; min-height: 0`
- `#cy` 用 `position: absolute; top/left/right/bottom: 0` 填满容器
- 图例 `position: absolute` 浮动在左下角
- 所有布局必须设 `fit: true` 和 `padding: 80`，确保图完整显示在画布内不溢出

### 9. 容错与兜底（确保 100% 稳定）

| 场景 | 兜底策略 |
|------|---------|
| 新增节点类型 | `getNodeTypeMeta()` 自动分配颜色和形状 |
| 新增 Namespace | `getNsColor()` 从兜底池自动分配 |
| 新增 Severity | `getSevColor()` 返回默认黄色 |
| 新增边类型 | `getEdgeStyle()` 返回默认灰色样式 |
| 节点 data 字段变更 | 详情面板自动展示所有字段（优先排序+自动追加） |
| JSON 缺逗号 | `fix_json_syntax()` 自动修复 |
| 虚拟节点 ID 前缀变更 | 默认创建 attack 节点，不丢弃边 |
| progress.json 新增 Phase | 显示 Phase ID（不显示名称），不崩溃 |
| 综合评分 | 动态计算，不硬编码 |

### 9.1 已知坑点（LLM 生成时必须避免）

| 坑点 | 原因 | 正确做法 |
|------|------|---------|
| **Pipeline 顺序错乱** | JavaScript `Object.keys()` 把纯数字键（"3","5","9"）排在字母键（"1a","2a"）前面 | 用显式 `PHASE_ORDER` 数组遍历，不依赖 `Object.keys()` 排序 |
| **getEdgeStyle 缺函数声明** | 原始 HTML 中 `getEdgeStyle` 是裸代码块（无 `function` 声明），依赖浏览器容错。LLM 生成时可能遗漏或多余闭合括号 | 必须写完整的 `function getEdgeStyle(edge) { ... }` 声明，用 `node --check` 验证语法 |
| **虚拟节点丢失导致边被过滤** | `attack_verify`/`attack_chain` 边的 `to_node`（如 `attack-socket-escape`、`CHAIN-001`）不在 nodes 中，`edges.filter()` 会丢弃这些边 | 在 `buildElements()` 中先从边数据派生虚拟节点，加入 `nodeIds` 集合后再过滤边 |
| **CSS 图例形状与实际不符** | Cytoscape 的 `hexagon`/`diamond`/`vee`/`star` 形状需要用 CSS `clip-path` 精确模拟，不能用 `transform:rotate` | 图例中每个形状用对应 `clip-path` polygon 坐标，与 Cytoscape shape 一一对应 |
| **浏览器底部空白** | `#cy` 用 `width:100%;height:100%` 但父容器没有明确高度 | `html,body` 设 `height:100%`，`body` 用 flex 垂直布局，`#cy` 用 `position:absolute` 填满 |
| **uses_sa 边缺失** | Phase 1a 只为高风险 SA 建 uses_sa 边，系统 SA（svclb/traefik/coredns 等）和 default SA 的 Pod→SA 关联缺失 | 从 `Pod.serviceAccountName` 按 `namespace+name` 匹配 SA 节点，派生 uses_sa 边 |
| **Pending Pod 缺 runs_on** | Pending 状态 Pod 的 `node` 字段为 `pending`，无对应 host 节点 | **这是正确的**——Pending = 未调度到任何节点。不创建虚拟 host，不派生 runs_on 边 |
| **Finding/Edge 数据重复** | `findings.json` 与 `findings_k8s.json` 有重复节点，`compliance.json` 与 `compliance_k8s.json` 有重复边 | `generate_viz.py` 合并时按 ID / from+to+type+atk_cand 去重 |
| **attack_verify 边去重丢失 LLM 来源** | 同一 attack 有多条 attack_verify 边（Phase 4a 无 source 字段 + Phase 4b 有 source=llm_reasoning），按 from+to+type 去重会把 Phase 4b 的边丢掉，导致所有 attack 都显示为 Phase 4a 模式库来源 | 去重 key 必须包含 `atk_cand` 字段，保留同一 attack 的不同 ATK-CAND 边 |
| **attack_verify 无 source 字段** | Phase 4a 的 attack_verify 边没有 `source` 字段，模板中 `e.attrs?.source` 返回 undefined 被跳过 | 无 source 字段视为 `pattern_library`（Phase 4a 默认） |
| **Phase 4b 改名导致悬空引用** | Phase 4b LLM 推理可能改变攻击名（如 `etcd-data-exposure` → `kine-db-exposure`），cross_ref 中保留原始假设名，attack_verify 中用新名，留下悬空引用 | 建立别名映射（`attackNameAlias`），将悬空引用重定向到已验证的新名节点 |
| **节点标签换行后仍截断** | Cytoscape `text-wrap: wrap` 配合过小的 `text-max-width` 和过短的截断长度，长标签换行后仍不完整 | 截断长度设为 50 字符，`text-max-width` 设为 160px |
| **Phase 高亮时无数据导致空图+杂乱边** | 某些 Phase 可能无检测结果（如 Docker 在无 Docker 环境中 64 条规则全部 NA），高亮时所有节点被淡化但边仍可见，显示为"只有线没有节点" | Phase 高亮前先检查该 Phase 是否有对应数据节点，无数据时全部淡化并显示提示信息（如"Docker 合规检测：64 条规则全部 NA（此环境无 Docker）"），切换 Phase 或点击空白时自动移除提示 |
| **攻击链步骤断裂** | chain steps 中有些 attack_name（如 `kine-bootstrap-token`）没有对应的 attack_verify 边，导致步骤串联时虚拟节点不存在 | 步骤串联前先遍历所有 steps，为无 attack_verify 的 attack_name 创建虚拟 attack 节点 |
| **派生边引用不存在的节点导致白屏** | 虚拟节点（如 `attack-kine-bootstrap-token`）在 `cyNodes` 数组计算完之后才创建，但派生边引用了它们。Cytoscape 遇到边引用不存在的节点会**静默崩溃**，整个图白屏无内容，不报错 | **所有虚拟节点必须在 `cyNodes` 计算之前创建，或创建后同步追加到 `cyNodes` 数组**。Cytoscape 初始化时 `elements` 中的每条边的 source 和 target 必须都有对应的节点元素，否则静默崩溃 |
| **合规违规无具体对象关联** | compliance 边全部从 host 出发，finding 的 judgment 文本中提到了具体 Pod/Container 但没有结构化边 | 解析 judgment 文本匹配 pod/container/SA 名称，派生 `对象→finding` 边 |
| **Finding 无 attack 关联** | Phase 3 只为精准备选建 cross_ref，Phase 4a/4b 验证了 attack 但没反向关联所有同 attack_surface 的 finding | 通过 finding 的 `attack_surface` 字段（AS-1~AS-5）映射到同攻击面的已验证 attack 节点 |
| **target-pod/* 虚拟节点孤立** | XREF-002 风险放大中的 `target-pod/{name}` 在 nodes 中不存在，创建为虚拟节点后无入边，看不出和哪个真实 Pod 关联 | 建立 `targetAlias` 映射，用 Pod 的短名和完整名匹配 `target-pod/*`，边重定向到真实 Pod，不创建虚拟节点 |
| **旋转事件绑定在元素创建之前** | 旋转按钮的 `addEventListener` 写在 `renderToolbar()` 调用之前，此时 `rotate-btn` 元素不存在，`getElementById` 返回 null，`null.addEventListener` 报错导致 IIFE 崩溃，整个图白屏 | **旋转事件绑定必须在 `renderToolbar()` 和 `renderChainPanel()` 调用之后** |
| **图初始显示过大** | 布局没有 `fit` 选项，图按原始坐标渲染，节点圆环撑满画布底部被截断 | 所有布局必须设 `fit: true` 和 `padding: 80` |
| **cross_ref 边看不出关联类型** | cross_ref 边只显示颜色，看不出是 XREF-001/002/003 哪种关联 | 边标签显示 `attrs.query` 值（XREF-001/002/003），节点详情入出边列表也显示 |
| **attack source 显示笼统** | cross_ref 引用的 attack 节点 source 显示 `cross_ref`，看不出具体是哪种 XREF | 从 cross_ref 边的 `attrs.query` 提取具体值（XREF-001/002/003）作为 source |

### 10. 星云旋转实现规范（V1.1）

```javascript
// 旋转原理：每帧计算每个节点新坐标，以画布中心为圆心旋转
// 不碰 canvas 本身，交互完全正常（点击/缩放/拖拽不受影响）

// step = 2π / (speed × 25)  // speed秒转一圈，每40ms一帧（25fps）
// 新x = cx + dx·cos(θ) - dy·sin(θ)
// 新y = cy + dx·sin(θ) + dy·cos(θ)

// 关键：变量名用 cy_h 避开 Cytoscape 实例名 cy
// 关键：事件绑定必须在 renderToolbar() 之后
```

### 11. 离线模式实现

```python
# 下载 cytoscape.min.js
urllib.request.urlopen("https://unpkg.com/cytoscape@3.30.2/dist/cytoscape.min.js")
# 内嵌到 HTML
html = template.replace("__CYTOSCAPE_LIB__", f'<script>{js_content}</script>')
```

离线版特征：无 `unpkg.com` 引用、cytoscape.js 内嵌在 `<script>` 块中、可完全离线使用。

## 参数说明

| 参数 | 简写 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--session-dir` | `-s` | 是 | — | GenCPT 会话目录路径 |
| `--output` | `-o` | 否 | `{session-dir}/knowledge_graph_viz.html` | 输出 HTML 路径 |
| `--offline` | — | 否 | 否 | 离线模式：内嵌 cytoscape.js（推荐） |
| `--online` | — | 否 | 是 | 在线模式：CDN（默认） |
| `--rotate` | — | 否 | 是 | 使用 V1.1 模板带星云旋转（默认） |
| `--no-rotate` | — | 否 | 否 | 使用 V1 模板不带旋转 |
| `--title` | `-t` | 否 | 自动生成 | HTML 页面标题 |

## 输出文件

| 文件 | 说明 |
|------|------|
| `{output}.html` | 自包含 HTML 文件，双击即开 |

## 在 Pipeline 中的集成

Phase 8c 完成后，入口 SKILL.md 追加执行：

```bash
python3 {套件根}/skills/graph-viz/generate_viz.py -s {session_dir} --offline
```

生成成功后输出路径：`{session_dir}/knowledge_graph_viz.html`

此步为可选能力，失败不阻塞 Pipeline。
