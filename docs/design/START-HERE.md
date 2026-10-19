# START HERE · 会话启动锚(任何新会话/上下文压缩后,先读本档,按读序走)

## 一句话现状(2026-10-21)
**P0 指挥台十四仗全落(T1-T14 全过,提交 97efd11/6a680b1 等)**——登录/跨仗时刻流/人话卡/说话开仗(真调 LLM+dry-run 演习)/两级播报/内联审批/发现卡/插话转向/全停/任务会话签/发现页+灰卡+复验/E2E 冒烟全绿。**下一步=P1**(平台面+enrich+证据仓+plan模式+引擎三小件 stop-hook/recursion-cap/session-memory);首场真仗点火需真授权书(引擎法,fail-closed)。

## 读序(权威优先级)
1. 本档 → 2. docs/design/2026-10-20-product-master-design-v4.md(现行总案:五层架构+新吸收六件 enrich/证据仓/事实图谱置信/YAML工具剧本包/旁路窗口/plan模式+norma17包对照+授权哲学) → 3. docs/research/2026-10-20-personal-full-read.md(四相全深档案:ARTEX前端24业务件/后端50路由+norma SDK/CSAI全件含15剧本/环境21页) → 4. docs/design/2026-10-20-system-mechanism-ledger.md(28机制对照) → 5. docs/superpowers/plans/p0-execution-ledger.md(施工态+全部裁决+工艺教训) → 6. docs/superpowers/plans/2026-10-20-p0-command-deck.md(P0 任务书 T1-T14,已毕) → 7. build-master-plan 落舱记(历史)

## 用户裁决全集(不可违背)
1. 产品=「和ARTEX/CSAI一样的产品」完整渗透平台;「AI自动挖洞,误报漏报都好,可控制」
2. 对话即指挥(opencode式);AI原生交互原则: AI能推断的不让用户填,AI只问真缺的
3. 两级播报;危险请示=中间档(可否决默认);单一常驻对话
4. 技术栈四节裁决: Vite+React SPA/FastAPI读面/SQLite只读索引/流量P0钩子→P1 Go边车;引擎Python保留零改
5. 「不要被现有实现限制,不合理就换,能力一件不丢」;全功能对照纪律(禁静默消失)
6. 授权哲学: 授权确认+预算两问+范围红线;拒「授权前置不反问」;不采C2/WebShell/wechat-robot
7. 「不能乱来,实事求是」: 没读就说没读;禁清单面冒充深读;禁虚报验收
8. 词汇律: 用户词表,答人话;禁无据的「超越ARTEX」
9. 「按专业的来就行」=专业裁量授权,但T5检查点(用户亲验)不可跳
10. 防遗忘机制=本档+落盘纪律,用户明确要求压缩前封舱

## 工艺铁律(含血泪教训)
- 测试: 后端 PYTHONPATH=cli python3 -m unittest discover -s tests/readface -p "test_*.py"(直收rc,禁管道尾echo);前端 cd web && npx vitest run > /tmp/vt.log 2>&1; echo $?(重定向收真rc+看Test Files行);E2E=cd tests/e2e && npx playwright test
- **PATH陷阱: shell里npx/node不在PATH——必须 export PATH=/opt/homebrew/bin:/usr/bin:/bin:$PATH**(教训#1假验收: npx not found却记PASS)
- 文档编辑: edit工具或python带assert(教训#2静默失败: replace没匹配不报错却报已落)
- 管道吞rc(教训#3): 一切复跑显式收rc
- 提交: pathspec-only;68律三验(全测绿+活体+落舱记);每次落地→账本→push
- 施工纪律: subagent-driven-development(每任务新舰+逐舰验收+裁决不停摆记账本);舰连亡则父接管(T12/T14 先例)
- 复验语义(T12 定): 指挥台复验=绑 EV 真重放(tanyin-replay 治理四门),判定如实回报;状态回写走验证官 settle 门,读面/桥不代写

## 调试通道(已备)
~/.tanyin/channels.json=glm-5.3@bigmodel coding端点(源:~/.dsh/.credentials.yaml WGEN001_API_KEY;仓外600,禁入仓禁入日志;已活体验证)。AI功能调试真调它。

## 关键端口/路径
8901=readface 指挥台(父代理常驻维护;**重启后重建**: python3 scripts/make_gl_review_home.py 再起服,命令见下);5173=vite dev(代理/api→8901);8900=旧webui(P1切走);夹具=tests/fixtures/G-r18;ARTEX源=/tmp/artex-look/ARTEX-main;CSAI=/Users/wgen/dsh-test/repos/CyberStrikeAI;ARTEX demo=artex-demo.mhtsec.com;用户本地ARTEX=8787(空数据)

## 8901 常驻服务一键重建(/tmp 根已三死于重启,T14 治本=仓内制造器)
```bash
cd /Users/wgen/redteam-agent
python3 scripts/make_gl_review_home.py   # 重建 /tmp/gl-review-home(G-r18 副本+钥链副件)
TANYIN_HOME=/tmp/gl-review-home READFACE_ALLOW_DEMO=1 nohup python3 -m uvicorn server.readface.main:app --host 127.0.0.1 --port 8901 > /tmp/gl-8901.log 2>&1 &
```
(不设 TANYIN_OPERATOR_KEY=演示登录可用;真钥匙登录则设之)

## 施工队列
**P0 全毕**: T1-T14 全过账(docs/superpowers/plans/p0-execution-ledger.md 逐仗提交号)。→ **P1**: 平台面(资产/报告/审批中心/技法库等 20 页 IA 实页化)+enrich+证据仓+plan模式+引擎三小件(stop-hook/recursion-cap/session-memory)+Go边车 → 首场真仗(需真授权书)
