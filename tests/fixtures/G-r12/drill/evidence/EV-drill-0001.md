---
id: EV-drill-0001
title: 演练EV:svc-login根200
source_type: command
observed_at: 2026-10-08T09:09:00Z
network_position: jumphost:range-attack-noop-1
preconditions:
  - 容器 range-attack-noop-1 可达 svc-login:8004
raw_request: |
  GET / HTTP/1.1
  Host: svc-login:8004
  User-Agent: G-r12-drill
expected:
  matchers:
    - {type: status, status: [200]}
    - {type: word, words: [login form]}
cleanup: 演练弃弹无副作用
pair_group: 
role: 
---
## 原始响应摘录（脱敏+定长）与判定依据
HTTP/1.0 200 <html>login form</html>
