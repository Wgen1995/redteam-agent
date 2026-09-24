---
id: EV-diff-authz-0001
title: 差分举证-user
source_type: command
observed_at: 2026-09-24T10:00:00Z
network_position: intranet
preconditions: []
raw_request: |
  GET /admin/api/users HTTP/1.1
  Host: app.intranet
  Authorization: {{vault:cred-3}}
expected:
  matchers:
    - {type: word, words: ["errorCode:00000"]}
    - {type: word, words: ['"total":42']}
    - {type: status, status: [200]}
  extractors:
    - {type: regex, name: total, regex: ['"total":(\d+)']}
cleanup: ''
pair_group: PG-g1-0002
role: user
---
## 原始响应摘录（脱敏+定长）与判定依据
  Authorization: {{vault:cred-3}}
