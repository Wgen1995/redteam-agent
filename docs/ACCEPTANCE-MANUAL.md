# 验收手册 v1(2026-10-18 补建——此前各波缺人类验收位,今起补齐)
用法: 每波收口后在本册加一条;你亲手跑「验收命令」,看到「算过」列的结果即验收。抽查律: 随机点名任一回执,AI 必须还原证据链。

## A1 账本之法(基座)
- 验收命令: cd /Users/wgen/redteam-agent && python3 -m cli.tanyin-ledger verify-chain --goal-dir ~/.tanyin/battles/battle-27(任取最新战)
- 算过: verify PASS 输出+链尾哈希;手工改一行→FAIL(防篡改实证)
## A2 工具卡 25 张(火力)
- 验收命令: python3 -m cli.tanyin_tools list && python3 -m cli.tanyin_tools show sqlmap
- 算过: 25 卡列出;sqlmap 卡显示 L3+审批门披露
## A3 技法库 50 卡(知识)
- 验收命令: python3 -m unittest tests.test_w3_cp_ingest -v 2>&1 | tail -3 && head -5 knowledge/cp-index.tsv
- 算过: Ran 8 tests OK;索引 50 行
## A4 时间线 O(1)+多战仲裁(并发)
- 验收命令: python3 -m unittest tests.test_timeline_o1_epoch tests.test_battle_registry 2>&1 | tail -1
- 算过: OK(18+15 测)
## A5 sqlmap 受控档+deepex(深挖)
- 验收命令: python3 -m unittest tests.test_engine_sqlmap tests.test_engine_deepex 2>&1 | tail -1
- 算过: OK(36+22 测)
## A6 单源化+退出码(工程)
- 验收命令: python3 docs/gen_counts.py --check && python3 -m unittest tests.test_gen_counts tests.test_exit_code_matrix 2>&1 | tail -1
- 算过: counts 一致+OK(6+15 测)
## A7 界面线(在航,收口后补条目)
- 当前: UI-1 六页换血/T1 漏洞详情/T2 播报/T3 四页签/T4 报告线 五舰在飞;收口即加 A7 条目(打开 8900 逐页主路径)
## A8 战士运行时 MVP(在航,最高优先)
- 收口即加: --dry-run 组上下文/假模型 E2E/R1-R5 质量律逐条
