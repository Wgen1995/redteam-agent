# CNPEN 素材落位（批次 5 T16——降级登记态）

计划五类素材执行期从客户素材库拷入本目录；执行期核验**五类均不在仓**（素材库在
仓外，且属本任务禁碰区），按计划降级登记通道处理：SOURCES.tsv 五笔 origin=cnpen
行 note=待补（KP-0001..KP-0005），**零蒸馏页产出——不造数据**。

| 类别 | 计划落位 | 就位后蒸馏去向 | 状态 |
|---|---|---|---|
| 测试全景图 | sources/cnpen/panorama/ | sources 登记指针（素材本体归 tests/fixtures，G-31 防库膨胀） | 待补 |
| 思路复盘 | sources/cnpen/retro/ | concepts 方法论原则页（errorCode 语义分析/前端 JS 是 API 说明书/微服务直连假设等） | 待补 |
| 测试记录 T1-T55 | sources/cnpen/records/ | precedents 先例链路页（CLIENT-NN 脱敏） | 待补 |
| 31 份黑盒漏洞单 | sources/cnpen/vuln-sheets/ | patterns ok-sample 样例页（注入深挖后才定级判定标准） | 待补 |
| BurpPOC 合集 | sources/cnpen/burp-poc/ | concepts 技法页 tool_params 节 | 待补 |

纪律：素材就位后对每类真实文件跑 `source-register --origin=cnpen --license=proprietary`
重登（新 KP 行取代待补行），再走 lint→approve→commit→export 流水；蒸馏页 vuln_class
一律 WSTG 词表键（防纯 Java 样本过拟合——T16 test_vocab_baseline_is_wstg_only 前向钉）。
