# 工作区数据契约

本文档定义工作目录结构规范、文件命名规范和 Phase 间数据传递规则。

---

## 1. 工作目录结构规范

每个渗透测试会话创建独立的工作目录，按 Phase 分子目录组织：

```
{session_dir}/
├── session_config.json                  # 会话配置
├── progress.json                        # Phase 进度状态机
├── task_list.json                        # 任务表
│
├── knowledge_graph/
│   ├── nodes/
│   │   ├── _index.md                    # 节点总索引
│   │   ├── hosts.json                   # 主机节点
│   │   ├── pods.json                     # Pod 节点
│   │   ├── containers.json              # 容器节点
│   │   ├── service_accounts.json        # SA 节点
│   │   ├── secrets.json                 # Secret 节点
│   │   ├── source_findings.json         # 源码安全发现
│   │   └── findings.json                # 合规违规 + 攻击命中
│   ├── edges/
│   │   ├── _index.md                    # 边总索引
│   │   ├── infra.json                   # 基础设施边
│   │   ├── compliance.json              # 合规边
│   │   ├── attack.json                  # 攻击边
│   │   ├── cross_ref.json              # 交叉关联边
│   │   └── source_edges.json            # 源码关联边
│   └── episodic_memory/
│       ├── session_history.md            # 跨会话历史
│       └── recommendations.md           # 晋升候选
│
├── evidence/
│   ├── recon/
│   │   ├── raw/                          # 原始 SSH 输出
│   │   ├── recon_summary.md
│   │   ├── source_analysis.md
│   │   ├── source_scan_stats.md
│   │   ├── recon_delta.md
│   │   └── summaries/                    # WU 摘要 JSON
│   ├── compliance/
│   │   ├── k8s/
│   │   │   ├── results.json
│   │   │   ├── summary.md
│   │   │   └── raw/
│   │   ├── docker/
│   │   ├── containerd/
│   │   ├── compliance_delta.md
│   │   └── summaries/
│   ├── cross-ref/
│   │   ├── cross_ref_summary.md
│   │   ├── risk_amplification.md
│   │   ├── prerequisite_signals.md
│   │   ├── history_priority.md
│   │   └── cross_ref_delta.md
│   ├── attack/
│   │   ├── pattern-hits.md
│   │   ├── reasoning-hits.md
│   │   ├── unmatched_signals.md
│   │   ├── insights.md
│   │   └── summaries/
│   ├── chains/
│   │   ├── chain_builder.md
│   │   ├── chain_verification.md
│   │   └── summaries/
│   ├── poc/
│   │   ├── poc_scripts/
│   │   ├── poc_readme.md
│   │   └── summaries/
│   ├── evolve/
│   │   └── evolve_report.md
│   └── qa/
│       ├── qa_summary_report.md
│       ├── qa_override_*.md
│       └── tool_upload_log.md
│
├── reports/
│   ├── compliance_checkpoint_report.md
│   ├── compliance_checkpoint_report.json
│   ├── compliance_report.md
│   ├── compliance_report.json
│   ├── attack_report.md
│   ├── attack_report.json
│   ├── poc_package/
│   ├── pentest_report.md
│   ├── pentest_report.json
│   └── coverage_report.md
│
└── tmp/
```

---

## 2. 文件命名规范

### 2.1 通用规则

- 所有文件名使用 **snake_case** 命名（小写字母 + 下划线）
- 日期格式：`YYYY-MM-DD`
- 时间戳格式：`YYYYMMDD-HHmmss`
- JSON 文件扩展名：`.json`
- Markdown 文件扩展名：`.md`
- 目录名使用 **snake_case**

### 2.2 特殊文件命名

| 文件 | 命名规则 | 说明 |
|------|---------|------|
| 索引文件 | `_index.md` | 每个目录一个，含目录内容索引 |
| 会话配置 | `session_config.json` | 含 server, mode, scope, env_fingerprint 等 |
| 进度状态 | `progress.json` | 含每个 Phase 的状态（pending/in_progress/complete） |
| 任务表 | `task_list.json` | 含 WU 列表和上下文预算 |
| WU 摘要 | `wu_{phase}_{batch}_{id}_summary.json` | 如 `wu_2a_1_001_summary.json` |
| QA 覆盖 | `qa_override_{phase}.md` | 如 `qa_override_2a.md` |
| 原始输出 | `{command_hash}_{timestamp}.txt` | 如 `a1b2c3_20260620-143052.txt` |
| ACK 文件 | `WU_{id}_ACK.json` | 写盘确认文件 |

### 2.3 禁止的命名

- 禁止使用中文文件名
- 禁止使用空格（用下划线替代）
- 禁止使用特殊字符（只允许 a-z, 0-9, _, -, .）
- 禁止使用相对路径引用（必须使用绝对路径或在 _index.md 中用相对路径）

---

## 3. Phase 间数据传递规则

### 3.1 MUST 输入输出表

每个 Phase 有明确的 MUST 输入和 MUST 输出。输入缺失时 Phase 不可启动；输出缺失时 Phase 不可完成。

| Phase | MUST 输入 | MUST 输出 |
|-------|----------|----------|
| **1a** | server, scope | knowledge_graph/nodes/（7个JSON）, knowledge_graph/edges/infra.json, evidence/recon/recon_summary.md, evidence/recon/raw/ |
| **1b** | source_path 或 source_url, source_type | knowledge_graph/nodes/source_findings.json, knowledge_graph/edges/source_edges.json, evidence/recon/source_analysis.md, evidence/recon/source_scan_stats.md |
| **2a** | knowledge_graph/nodes/（Phase 1a 输出）, scope 含 k8s | evidence/compliance/k8s/results.json, evidence/compliance/k8s/summary.md, knowledge_graph/nodes/findings.json（k8s 部分）, knowledge_graph/edges/compliance.json（k8s 部分） |
| **2b** | 同上, scope 含 docker | evidence/compliance/docker/（同结构） |
| **2c** | 同上, scope 含 containerd | evidence/compliance/containerd/（同结构） |
| **3** | knowledge_graph/edges/compliance.json, knowledge_graph/nodes/findings.json, 三库文件 | knowledge_graph/edges/cross_ref.json, evidence/cross-ref/（4个MD文件） |
| **4a** | 合规结果 + 交叉关联 + attack-patterns/_index.md | evidence/attack/pattern-hits.md, evidence/attack/unmatched_signals.md, knowledge_graph/edges/attack.json |
| **4b** | 未匹配信号 + 交叉关联 + 攻击面模型 + 知识图谱 | evidence/attack/reasoning-hits.md, evidence/insights.md, knowledge_graph/edges/attack.json（追加）, episodic_memory/recommendations.md |
| **5** | attack.json + cross_ref.json + findings.json | evidence/chains/chain_builder.md, knowledge_graph/edges/cross_ref.json（追加 attack_chain 边） |
| **6** | 链式攻击数据 + 知识图谱 | evidence/chains/chain_verification.md |
| **7** | 验证完成的攻击链 + POC 数据 | evidence/poc/poc_scripts/ + poc_readme.md |
| **8a** | 合规数据 | reports/compliance_report.md + .json |
| **8b** | 攻击数据 + POC 包 | reports/attack_report.md + .json + poc_package/ |
| **8c** | 8a + 8b 报告 + 知识图谱 + insights + session_history | reports/pentest_report.md + .json, reports/coverage_report.md, evidence/qa/qa_summary_report.md |
| **9** | insights.md + session_history.md + _index.md + attack-hypotheses.md | attack-patterns/新增 SKILL.md, _index.md 更新, evidence/evolve/evolve_report.md |

### 3.2 数据传递规则

1. **写盘优先**：每个 work unit 完成后立即写盘，不持有数据等待。SSH 输出立即写入 `evidence/` 目录，分析结果立即写入知识图谱和报告文件
2. **摘要上行**：sub-agent 只返回 ≤500 tokens 的结构化摘要给 supervisory-agent。原始数据写盘，摘要格式：
   ```
   {work_unit_id} | {status} | {summary} | {critical_findings} | {files_written} | {context_used} | {issues}
   ```
3. **按需读取**：不读全量文件。先用 `_index.md` 定位，只读当前 work unit 需要的部分。Read 完成后分析结果写盘，释放上下文
4. **批次控制**：每个 work unit 上下文预算 ≤100k tokens。SSH 命令分批执行（5-7 条/批，间隔 2 秒）
5. **去重规则**：写入知识图谱时立即去重（读 → 合并 → 写回），去重 key 见设计文档 16 节

### 3.3 知识图谱边文件写入约定

| 边类型 | 写入文件 | 写入时机 | 去重 key |
|-------|---------|---------|---------|
| infra | infra.json | Phase 1a | from_node + to_node + edge_type |
| compliance | compliance.json | Phase 2a/2b/2c | from_node + to_node + edge_type |
| attack | attack.json | Phase 4a/4b | from_node + attack_name + source |
| cross_ref | cross_ref.json | Phase 3 | from_node + to_node + reason 语义 hash |
| attack_chain | cross_ref.json（追加） | Phase 5 | chain_id |
| source | source_edges.json | Phase 1b | from_node + to_node + edge_type |

### 3.4 进度状态机

`progress.json` 记录每个 Phase 的状态：

```json
{
  "session_id": "sess-20260620-001",
  "phases": {
    "1a": {"status": "complete", "completed_at": "...", "wu_progress": {"WU-001": "complete"}},
    "1b": {"status": "pending"},
    "2a": {"status": "in_progress", "resumable_from_batch": 2},
    "..."
  }
}
```

状态转换规则：

| 当前状态 | 条件 | 新状态 |
|---------|------|--------|
| `pending` | 开始执行 | `in_progress` |
| `in_progress` | 所有 MUST 输出文件存在且非空 | `complete` |
| `complete` | 检查 MUST 输出是否完整 | 跳过 → 读已有结果；缺失 → 重新执行 |
| `in_progress` (断点续传) | 从 `resumable_from_batch` 继续 | `in_progress` |