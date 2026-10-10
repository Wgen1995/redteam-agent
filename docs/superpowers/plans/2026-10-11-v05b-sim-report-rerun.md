# 2026-10-11 v0.5b 仿真补债+报告最后一公里批

- G1 sim 场景C/D：budget 执法全链（超限→BUDGET-ENFORCE+收尾令重启）与 ask:human 往返
  （ask.md→WAIT 停表→answer.md→ASK-ANSWERED 注入）——还 v0.5a F3/F5「纯函数已测全链未验」的债。
- G2 CVSS 计算器（v3.1 base 纯函数）+report_render._FIX_MAP 扩全（xss/ssrf/rce/deser/idor/lfi/open-redirect）。
- G3 干净重跑协议 scripts/rerun.py：同任务书+同字典 N≥3 战，settle 报告 recall 行聚合
  （mean/std/min/max），n=1 叙事→统计面第一步；--dry 用假报告走全链。
- 改期 v0.6（诚实重排，非缩水）：wall_clock 双轨（schema 大迁移单批）、DENYLIST v2+rate+UA
  （安全批）、runtime.py 抽取（工程批）、vuln-agent 接线/codex E2E（外部环境+用户侧）。
