# P0 执行账本(subagent-driven-development)
任务态: T1派/T2派/T3-T14待。裁决记录于本档。
检查点: T5 落地后停,请用户上 8901 亲验(用户钦定质量阀)。
- T1 PASS(f3d411f): 4文件232行/9测试独立复跑RC=0/hmac比较+会话过期清理+HttpOnly抽查过;下游契约=POST /api/auth/login {"key"}→200{"ok","demo"}+cookie|401{"error":"密钥不对"}。
- T2 PASS(9cffdb2): 15用例独立复跑RC=0/cli零改动diff=空;approvals id=sha256(revert_cmd)即签名链command-hash(T8用)。
- T3 PASS(eb32d1e): vitest 3/3+build绿;裁决=shadcn CLI不适用环境,手搓ui件同构(cva+cn);GL-DS令牌自login.html提取零漂移。
- Ruling T4: 徽章数据需读面端点,T4内增 routers/overview.py(GET /api/overview: 进行中仗数/在跑士兵/待审批数,ledger_reader供给,2用例)——计划T2只建了库未建面,折叠入T4领地(新文件不相交)。
- Ruling(用户掣令): v3降草案;T4落地后T5+冻结,待全量深析+重设计过审后续。补课战役=ARTEX前端内部件→后端全包→CSAI全件→环境(8787)→重综合设计v4。
- T4 PASS(407e7dd读面+fca7a1c壳): overview 2/2+回归26/26独立复跑RC=0;vitest真验(修正PATH后)9/9;活体8902烟测过;两处必要联动触碰(chat黄条/login用例3)报备合理;报备「四节vs20页」按v3三组裁决正确。
- 工艺教训#3: 复跑命令管道吞rc(npx缺node显示VRC=0假绿)——复跑必须显式PATH+直收rc,禁管道尾接echo。
- CSAI 15剧本全毕: 4深读+11结构核验,统一模式=frontmatter+授权状态+优先级+输入前置硬约束(缺字段返回清单禁猜测)+禁止项——「计划步骤自洽律」吸收进我方意图派单。
- Ruling: 用户「按专业的来就行」=解冻T5+,专业裁量授权;T5落地后仍停请用户上8901亲验(钦定检查点不变)。
- Ruling: 用户裁定 v4 总案「过」——设计正式定稿,v3/草案地位终结,P1 排期以 v4 为准。
- Ruling+落地: 用户令「调试功能用当前LLM密钥」——已接。来源=~/.dsh/.credentials.yaml 的 WGEN001_API_KEY(智谱 coding 端点,glm-5.3);写入 ~/.tanyin/channels.json(仓外,chmod600,密钥零入日志/仓);活体验证: 200+「收到」+usage计费。T6起意图解析/AI确认真调此通道;注意该文件三密钥(DEEPSEEK/WGEN001/CODING_PLAN)——只用WGEN001,首抓DEEPSEEK得401已纠。
