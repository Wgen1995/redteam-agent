# evolve 三库一致性检查

> 本文件为 `skills/evolve/SKILL.md` 进化完成后的三库一致性检查参考。核心工作流见 SKILL.md。

---

## 一致性维护

进化完成后执行 LLM 语义检查三库一致性。三库指：
1. `attack-patterns/_index.md`（模式索引）
2. `attack-patterns/` 目录下的实际文件（模式 SKILL.md）
3. `hypothesis-libraries/attack-hypotheses.md`（假设卡片）

### 检查项

| 检查项 | 检查方法 | 不一致处理 |
|--------|---------|-----------|
| _index.md 条目 ↔ 实际文件 | _index.md 中每个条目的路径字段指向的文件必须存在 | 文件缺失 → 从 _index.md 移除该条目或标记为缺失 |
| 实际文件 ↔ _index.md 条目 | attack-patterns/ 目录下每个 SKILL.md 必须在 _index.md 中有条目 | _index.md 缺条目 → 新增条目 |
| _index.md 条目 ↔ 假设卡片 | 每个模式的 hypothesis_refs 字段引用的假设卡片必须在 attack-hypotheses.md 中存在 | 假设卡片缺失 → 新增假设卡片或移除引用 |
| 假设卡片 ↔ _index.md 条目 | attack-hypotheses.md 中每个关联模式字段引用的模式必须在 _index.md 中存在 | 模式缺失 → 从假设卡片移除关联或标记为孤儿假设 |
| 编号连续性 | ATK-HYP 编号连续无遗漏 | 编号断档 → 在 evolve_report.md 中记录断档位置 |
| frontmatter 字段完整性 | 每个模式 SKILL.md 的 frontmatter 必须包含 name、source、confidence、hit_count、last_hit、stale、platforms、attack_surface 字段 | 字段缺失 → 补充默认值 |

### 输出

一致性检查结果写入 `evidence/evolve/evolve_report.md` 第 7 节统计部分。

不一致项列表（如有）附加在 evolve_report.md 末尾：

```markdown
## 三库不一致项

| 序号 | 不一致类型 | 位置 | 详情 | 处理动作 |
|------|-----------|------|------|---------|
| 1 | _index.md 条目无对应文件 | _index.md 第 {N} 行 | 模式 {pattern-name} 路径指向的文件不存在 | 从 _index.md 移除条目 |
```
