# P0 执行账本(subagent-driven-development)
任务态: T1派/T2派/T3-T14待。裁决记录于本档。
检查点: T5 落地后停,请用户上 8901 亲验(用户钦定质量阀)。
- T1 PASS(f3d411f): 4文件232行/9测试独立复跑RC=0/hmac比较+会话过期清理+HttpOnly抽查过;下游契约=POST /api/auth/login {"key"}→200{"ok","demo"}+cookie|401{"error":"密钥不对"}。
