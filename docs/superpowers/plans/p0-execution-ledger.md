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
- 调试通道终态: 用户亲授钥(user-glm,glm-5.3@bigmodel coding)+三协议端点(anthropic/coding/v1);此刻双端点429(疑与驱动本会话的同端点流量互挤,备用钥分钟级前同端点两发200)——已按引擎有序链落双钥接力(user-glm优先/wgen001垫后,~/.tanyin/channels.json 仓外600)。T6点火时真调即验,不阻塞T5。
- T5 PASS(de6069a指挥流): 独立复跑PY36/36+VT17/17+BUILD=0引擎零改;活体8901真数据(stream/warboard/badge/翻页)。工艺裁决两条入册: ①G-r18实存4处ts时钟倒挂→弃「每仗取limit归并」改全量timeline_tail+(ts,key)确定全序开窗(翻页严格无重无漏,715行全链验证) ②next_cursor=入参∪本页末key(否则未出战之仗重现最新行)。检查点服务已起: 8901+演示模式+G-r18全量合成仗。等用户亲验。
- 检查点判定: 用户「目前看还行」=骨架过;痛点=数据看不懂(原账本黑话)/无操作路径——正是T6(说话开仗)与T7-T9(两级播报/时刻卡)的既定范围,非设计缺口。T6即刻出航。
- T6 PASS(a612d7a说话开仗): 独立复跑PY53/53+VT24/24+BUILD=0+引擎零改;活体真钥glm-5.3全链(意图/确认卡/dry-run回执battle-43/零写入/缺预算只问缺的)。工艺注记: say客户端按TANYIN_HOME找channels.json——检查点服务起在重定向根时须同根备channels(已补/tmp/gl-review-home/channels.json 600)。8901常驻由父代理自持(T6舰沉服务随亡教训)。T7出航。
- T7 PASS(5544d2a两级播报): 独立复跑VT61/61+BUILD=0;活体50卡DOM实证(发现红/关卡绿/更替琥珀)。父热修757d84e: SPA深链回退(/chat刷新200,/api不兜,穿越拒,5测,随修随部8901)。T8出航。
- T8 PASS(86a75b3内联审批): 独立复跑PY78/78+VT75/75+BUILD=0+cli零改;活体真批真拒双向+链verify过+DOM九断言;越界ledger_reader+12行(决定回链出队=引擎W6同律)正当入册。T9出航。
- T9 PASS(01c6de1发现时刻卡): 独立复跑PY83/83+VT95/95+BUILD=0+引擎零改;活体6卡升级DOM实证(绿徽为主灰如实);偏差2条(where/evidence通道+REPAIRED词表透传)零假数取向正当。T10出航。
- T10 PASS(ae20c56插话转向): 独立复跑PY110/110+VT103/103+BUILD=0+引擎零改;活体真steer+真halt入链+DOM实证。CLI面勘定: steer/stop单源=cli/warrior/steer.py write_steer/write_stop(桥进程内调,goal锁单写者)。T11出航。
- T11 PASS(073975b任务·会话签): 独立复跑PY126/126+VT116/116+BUILD=0+引擎零改;活体三仗列表→详情→会话卡→组流DOM实证(steer原文逐字可见);裁量2条(main.py挂载先例/列表10s轮询如实)入册。T12出航。
- 重启事故: 电脑重启→T12前舰亡(零落件)/夹具根失/服务失;已恢复(battle-1=G-r18+channels 重铺,8901 重启),T12重派。教训: 夹具根在/tmp怕重启——T14收官时评估挪仓内tests区。
- T12 PASS(97efd11发现页+灰卡,父代理自做): 前舰二连亡(重启+无音讯)裁定接管。py10+vt7先红后绿,全回归绿,活体: 76发现/灰卡1张/详情EV+复放史/真reverify→tanyin-replay治理门真回REJECT授权窗口外(诚实不越权)。桥修2bug: server包import断→本目录引入式(approve同律);latest_by键=元组非裸串。铁律新证: 复验判定如实回报,状态回写走验证官settle门,桥不代写。
