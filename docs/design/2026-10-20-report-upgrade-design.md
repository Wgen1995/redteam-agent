# 功能26 报告生成·补件设计(定稿)· 2026-10-20

> 家底已核(29测绿): report_lint.py(Burp可贴四规则+双指纹+sign_gate聚合+pass.json签发+禁空话句式)/report_artifacts.py(findings.json全量生命周期+SARIF 2.1.0仅verified+narrative_filter+write_all九段FD渲染)——**机械骨架已建成**。本稿=ARTEX全量清点翻出的三件补件,不重造骨架。

## 补件一: 证据角色与版本(ARTEX证据中心工程吸收)
现况: EV卡四要素门(raw_request/raw_response/时间/环境)+fd↔EV关联已有。
补: ①每个finding的证据清单带**角色**(proof漏洞证明/baseline正常对照/verification补充验证/supporting辅助)与顺序;②finding证据集带**版本号**(任何绑定增删改=版本+1);③报告渲染必须携带evidence_version,**过期版本拒写**(证据变了报告必须重读重写——机械门,不靠自觉);④证据变化后已有报告标**待更新**(不静默过期)。
判: 我们的双指纹门+ARTEX的版本拒写=合体后强于两家任一。

## 补件二: 报告员兵种(ARTEX报告Agent吸收+我们验证官哲学校准)
ARTEX: 发现入库→自动触发报告Agent→它自己核对流量→绑定→按最新版本写报告。
我们: **报告员=军团新兵种**(六维配置: LLM道任意/技能=报告写作卡/权限=只读账本+EV/执行后端=warrior)。纪律: **报告员只写,机器把关**——它的产物必须过既有sign_gate全门(九段/Burp可贴/双指纹/redact-scan/禁空话),不过=打回。与验证官(非LLM)分工: 验证官裁真假,报告员写叙述,机械门签发——三层各司其职。
触发: 战役收口时自动+人工随时可点。

## 补件三: 过期检测与增量重渲染
rerender同输入同输出已钉死。补: 渲染时快照各finding的evidence_version入report manifest;下次渲染前比对——版本漂移=输出「证据已变化,待重写」清单(哪几个finding的证据动了),不渲染半新半旧报告。

## 对比(67律)
ARTEX: 版本控制+报告Agent(最强竞品,全吸收)/VulnClaw: findings.json同型(已吸收)/cyber-audit: OKF摘要节(已吸收)+两轮修复帽(借: 报告员被打回≤2轮后转人工)/Codex: SARIF字段族(已有双指纹,不另加)。**我们独有**: 签发门聚合机械把关(ARTEX零此层)+Burp可贴raw+禁空话句式。
## 建序与估算
①证据角色+版本+拒写门(~350行,report_artifacts+lint各半) ②报告员兵种模板+触发(~250) ③过期检测manifest(~150)+两轮修复帽(~50)≈**800行**,TDD,过report_lint既有29测+新增测。

## 你看到什么(人话)
报告页: 每个漏洞带「证据袋」(哪几条证据、各是什么角色、版本号);「证据变了,报告待重写」黄条;报告员写的叙述段落标记来源;签发凭证(几道门全过的证明)。
