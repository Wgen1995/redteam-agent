# evolve 自净机制与 hit_count 规则

> 本文件为 `skills/evolve/SKILL.md` 步骤 5 的自净和降级规则参考。核心工作流见 SKILL.md。

---

## 步骤 5：自净和降级

遍历 `attack-patterns/_index.md` 中所有 `source=learned` 的模式，根据 hit_count 和未命中连续次数执行自动调整。

### 5.1 升级规则

| 条件 | 动作 |
|------|------|
| learned 模式 hit_count ≥5 且跨 ≥2 环境（session_history 中记录了至少 2 个不同 host_fingerprint 的命中） | confidence 升级为 `high` |

升级后更新模式 SKILL.md 的 frontmatter `confidence=high`，更新 `_index.md` 和 `_learned_index.md` 对应条目。

### 5.2 降级规则

| 条件 | 动作 |
|------|------|
| learned 模式连续 5 次会话未命中 | confidence 降级为 `medium`（如果当前是 high） |
| learned 模式连续 10 次会话未命中 | 标记 `stale=true`（标记但不归档，仍保留在模式库中） |
| learned 模式连续 15 次会话未命中 | 使用当前环境的用户交互工具询问用户是否归档到 `attack-patterns/_archived/` |

**降级判定方法**：
- 从 `session_history.md` 中提取最近 N 次会话的记录
- 对每个 learned 模式，查找最近一次命中的会话序号
- 从最近一次命中会话到当前会话，计算"连续未命中次数"
- 连续未命中次数 = (当前会话序号 - 最近命中会话序号)
- 若该模式在 session_history 中无任何命中记录，连续未命中次数 = session_history 中记录的总会话数

**归档处理**：
- 用户选择归档 → 将模式 SKILL.md 移动到 `attack-patterns/_archived/{attack-surface}/{pattern-name}/SKILL.md`
- 在 `_index.md` 中移除该条目，在 `_learned_index.md` 中标记"已归档"
- 在 `_archived/` 目录下创建 `_archived_index.md` 记录归档模式
- 用户选择不归档 → 重置 stale 标记为 false，hit_count 保持不变，记录用户决策

### 5.3 manual/curated 模式处理

对 `source=manual` 或 `source=curated` 的模式：
- **只更新 hit_count 和 last_hit**（如果本次会话命中了该模式）
- **不执行降级或归档**（manual/curated 来源永远保持 confidence=high）
- 不修改 confidence 值

---

## 进化报告格式

在 `evidence/evolve/evolve_report.md` 中输出完整的进化报告：

```markdown
# 进化报告 — Phase 9

> 会话时间：{本次会话时间}
> 会话目录：{session_dir}

## 1. 晋升列表

| 序号 | 候选 ATK-CAND | 攻击面 | 新模式名称 | 门槛检查结果 | 用户审批 | 路径 |
|------|--------------|--------|-----------|-------------|---------|------|
| 1 | ATK-CAND-XXX | {攻击面} | {pattern-name} | ①✅ ②✅ ③✅ ④✅ | 添加 | {attack-surface}/{pattern-name}/_learned/SKILL.md |

## 2. 降级列表

| 模式名称 | 攻击面 | 原置信度 | 新置信度 | 原 stale | 新 stale | 降级原因 | 动作 |
|---------|--------|---------|---------|---------|---------|---------|------|
| {pattern-name} | {attack-surface} | high | medium | false | false | 连续 5 次未命中 | 降级 |
| {pattern-name} | {attack-surface} | medium | medium | false | true | 连续 10 次未命中 | 标记 stale |

## 3. 升级列表

| 模式名称 | 攻击面 | 原置信度 | 新置信度 | 升级原因 |
|---------|--------|---------|---------|---------|
| {pattern-name} | {attack-surface} | medium | high | hit_count={N} 跨 {N} 环境 |

## 4. 归档列表

| 模式名称 | 攻击面 | 归档原因 | 用户审批 | 归档路径 |
|---------|--------|---------|---------|---------|
| {pattern-name} | {attack-surface} | 连续 15 次未命中 | 归档 | _archived/{attack-surface}/{pattern-name}/ |

## 5. 变体匹配列表

| 候选 ATK-CAND | 匹配的现有模式 | 匹配维度 | hit_count 更新 |
|---------------|--------------|---------|---------------|
| ATK-CAND-XXX | {pattern-name} | 前置条件子集 + 攻击路径相同 | {N} → {N+1} |

## 6. 暂存观察列表

| 候选 ATK-CAND | 未满足门槛项 | 暂存原因 | 下次需要的数据 |
|---------------|------------|---------|--------------|
| ATK-CAND-XXX | ④ 跨会话命中 ≥2 次 | 历史仅 1 次命中 | 需在另一个环境验证 |

## 7. 统计

| 指标 | 数值 |
|------|------|
| 候选发现总数 | {N} |
| 可晋升数（4 项全满足） | {N} |
| 用户批准晋升数 | {N} |
| 变体匹配数 | {N} |
| 暂存观察数 | {N} |
| 拒绝数 | {N} |
| 升级数（medium → high） | {N} |
| 降级数（high → medium） | {N} |
| 标记 stale 数 | {N} |
| 归档数 | {N} |
| 三库一致性检查 | 通过 / 不通过（{不一致项数量}项） |
```
