# 提交合格样例（submission-ok）——契约 07 顶层 9 字段全样例＋authz 单元模板

```json
{
  "intent_id": "INT-g1-0007",
  "engine": "web-blackbox",
  "status": "done",
  "facts": [
    {"kind": "authz", "target": "app.intranet/admin/api/roles", "detail": "各角色 403 一致（回归基线）", "confidence": 0.9}
  ],
  "findings": [
    {"title": "admin 数据可被 user 角色读取（BOLA）", "confidence": "C2", "impact": "高",
     "exploitation_status": "suspected", "auth_context": "CRED-g1-0003",
     "reproducible_steps": ["user 会话 GET /admin/api/users → 200 errorCode:00000"],
     "evidence_refs": ["EV-g1-0003", "EV-g1-0004"], "location": "app.intranet/admin/api/users",
     "dedup_key_proposed": "AST-g1-0004+wstg-authz-bola", "network_position": "intranet",
     "preconditions": ["持有有效会话 {{vault:cred-3}}"],
     "expected_matcher": {"matchers": [{"type": "word", "words": ["errorCode:00000"]},
                                        {"type": "status", "status": [200]}],
                          "extractors": [{"type": "regex", "name": "total", "regex": ["\"total\":(\\d+)"]}]}}
  ],
  "assets": [
    {"type": "endpoint", "value": "app.intranet/admin/api/users", "meta": "protected"}
  ],
  "edges": [
    {"kind": "evidences", "source_id": "FD-g1-0002", "target_id": "EV-g1-0003"}
  ],
  "creds": [
    {"kind": "session", "role": "user", "username_ref": "user1", "secret_ref": "{{vault:cred-3}}",
     "scope_asset": "AST-g1-0004", "permitted_actions": "read"}
  ],
  "operations_log": "operations.log"
}
```

## authz finding 单元模板（差分正对）
同端点实验组/对照组两 EV 共享 pair_group（PG 由总控铸造）；auth_context=CRED-<id>；
expected_matcher 必填角色/数据标识（word=errorCode 等业务标识+status）——P4 盲重放按此验证。
