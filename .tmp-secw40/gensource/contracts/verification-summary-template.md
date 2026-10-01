# verification-summary.md 模板（v0.9.0）

Gate-1 方程「三事实源一致性」用 `candidates.tsv` + `findings/machine-fields.json` + `report.md` 三事实源做 candidate_id 一致性校验（不读本文件）；本文件（`verification-summary.md`）由宿主 shell [`host-reconciliation-commands.md`](host-reconciliation-commands.md) §4c 对账块生成/校验。格式必须含确定性 ID（正则 `C-\\d{5}-\\d{5}-[0-9a-f]{8}`），禁止占位。

```markdown
# 验证与定级摘要

stage_result: completed
candidate_count: N
confirmed_count: N
unconfirmed_count: N
refuted_count: N

## 根因组 RCG-XXX
### C-{sink_seq}-{source_seq}-{sig8}: 标题
- verification_verdict: confirmed
- three_elements: controllable/reachable/failed_control（每项附证据行号）
- confidence_score: {value, threshold, threshold_passed, rationale}
- final_severity: 等级
- cvss_vector: CVSS:3.1/...
```

**铁律**：candidate_id 必须与 candidates.tsv 完全一致（「三事实源一致性」）；无候选时写 zero-input 终态（candidate_count: 0）。
