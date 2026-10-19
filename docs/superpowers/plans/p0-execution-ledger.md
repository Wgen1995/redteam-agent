# P0 执行账本(subagent-driven-development)
任务态: T1派/T2派/T3-T14待。裁决记录于本档。
检查点: T5 落地后停,请用户上 8901 亲验(用户钦定质量阀)。
- T1 PASS(f3d411f): 4文件232行/9测试独立复跑RC=0/hmac比较+会话过期清理+HttpOnly抽查过;下游契约=POST /api/auth/login {"key"}→200{"ok","demo"}+cookie|401{"error":"密钥不对"}。
- T2 PASS(9cffdb2): 15用例独立复跑RC=0/cli零改动diff=空;approvals id=sha256(revert_cmd)即签名链command-hash(T8用)。
- T3 PASS(eb32d1e): vitest 3/3+build绿;裁决=shadcn CLI不适用环境,手搓ui件同构(cva+cn);GL-DS令牌自login.html提取零漂移。
- Ruling T4: 徽章数据需读面端点,T4内增 routers/overview.py(GET /api/overview: 进行中仗数/在跑士兵/待审批数,ledger_reader供给,2用例)——计划T2只建了库未建面,折叠入T4领地(新文件不相交)。
