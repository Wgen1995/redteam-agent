# START HERE · 会话启动锚(任何新会话/上下文压缩后,先读本档,按读序走)

## 一句话现状(2026-10-20 深夜)
四相补课全毕→**v4 总案已过审(用户裁定「过」)**→解冻施工+专业裁量授权。T1-T4 已落真验;**T5 指挥流舰在飞(id a8f2c029-f85a-4be2-8e19-7c10f057d075)**;T5 落地验收后**必须停,请用户上 8901 亲验指挥台**(我向用户的承诺,不可跳过)。

## 读序(权威优先级)
1. 本档 → 2. docs/design/2026-10-20-product-master-design-v4.md(现行总案:五层架构+新吸收六件 enrich/证据仓/事实图谱置信/YAML工具剧本包/旁路窗口/plan模式+norma17包对照+授权哲学) → 3. docs/research/2026-10-20-personal-full-read.md(四相全深档案:ARTEX前端24业务件/后端50路由+norma SDK/CSAI全件含15剧本/环境21页) → 4. docs/design/2026-10-20-system-mechanism-ledger.md(28机制对照) → 5. docs/superpowers/plans/p0-execution-ledger.md(施工态+全部裁决+工艺教训) → 6. docs/superpowers/plans/2026-10-20-p0-command-deck.md(P0 任务书 T1-T14) → 7. build-master-plan 落舱记(历史)

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
- 测试: 后端 python3 -m unittest tests.readface.xxx(直收rc,禁管道尾echo);前端 cd web && npx vitest run > /tmp/vt.log 2>&1; echo $?(重定向收真rc+看Test Files行);E2E=Playwright channel="chrome"
- **PATH陷阱: shell里npx/node不在PATH——必须 export PATH=/opt/homebrew/bin:/usr/bin:/bin:$PATH**(教训#1假验收: npx not found却记PASS)
- 文档编辑: edit工具或python带assert(教训#2静默失败: replace没匹配不报错却报已落)
- 管道吞rc(教训#3): 一切复跑显式收rc
- 提交: pathspec-only;68律三验(全测绿+活体+落舱记);每次落地→账本→push
- 施工纪律: subagent-driven-development(每任务新舰+逐舰验收+裁决不停摆记账本)

## 关键端口/路径
8901=readface(uvicorn,T1起);8902=T4烟测用过;5173=vite dev(代理/api→8901);8900=旧webui(P1切走);夹具=tests/fixtures/G-r18;ARTEX源=/tmp/artex-look/ARTEX-main;CSAI=/Users/wgen/dsh-test/repos/CyberStrikeAI;ARTEX demo=artex-demo.mhtsec.com;用户本地ARTEX=8787(空数据)

## 施工队列
T5在飞(指挥流:跨仗合并时间线/战况板三格/断线重连/翻页/仗过滤) → T5验收+**用户亲验检查点** → T6说话开仗(chat-say/意图解析/AI确认/点火dry_run) → T7两级播报 → T8内联审批 → T9发现时刻卡 → T10插话转向 → T11会话签 → T12灰卡 → T13 E2E → T14收官三验 → P1(平台面+enrich+证据仓+plan模式+引擎三小件)

