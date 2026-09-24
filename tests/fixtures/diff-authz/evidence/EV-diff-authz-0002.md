---
id: EV-diff-authz-0002
title: 差分举证-anonymous
source_type: command
observed_at: 2026-09-24T10:00:00Z
network_position: intranet
preconditions: []
raw_request: |
  GET /admin/api/users HTTP/1.1
  Host: app.intranet
expected:
  matchers:
    - {type: word, words: ["403", "anonymous-denied"]}
    - {type: status, status: [403]}
cleanup: ''
pair_group: PG-g1-0002
role: anonymous
---
## 原始响应摘录（脱敏+定长）与判定依据
  Host: app.intranet
