# 代码地图册(2026-10-18 建,用户令「不要靠记忆」——一切源码位置以本册为准,新仓库即更)
## 我们的资产
| 仓 | 路径 | 说明 |
|---|---|---|
| GraphLed 主仓 | /Users/wgen/redteam-agent | 账本/执法/引擎/界面/UI三舰在航 |
| ZhuLong 本地仓(只读) | /Users/wgen/Documents/AI For Security & Compliance/ai-assisted-security-verification-platform | 一代管理台,件按竞优搬;部署实例=远端 |
## 五产品源码(全部用户授权)
| 产品 | 路径 | 备注 |
|---|---|---|
| ARTEX 开源版 | /Users/wgen/dsh-test/repos/ARTEX (+artex.tar.gz) | 2026-10-08 转闭源前的快照;企业版Pro=闭源不可得;planner.go473/worker.go535=调度双核 |
| CyberStrikeAI(被微步收购,7800星) | /Users/wgen/dsh-test/repos/CyberStrikeAI (+cs.tar.gz) | 四编排/工具卡/HITL |
| VulnClaw | /Users/wgen/redteam-agent/.research/repos/VulnClaw | 713文件 3b71e26;agent/5873行=可移植大脑 |
| multica | /Users/wgen/redteam-agent/.research/repos/multica | 118表/37路由;dsh.go=DSH适配器 |
| js.tar.gz | /Users/wgen/dsh-test/repos/js.tar.gz | 待解包勘明(疑ZhuLong前端或CSAI资产) |
## 活体爬档(2026-10-18 起)
.research/liveharvest/{artex(23页全),csai(登录口待破),zhulong(远端1995可达)} + 研究档 docs/research/*artex*
## 新参考(RedAgents 生态,2026-10-18 情报)
| 名目 | 状态 |
|---|---|
| 衍迹(chainreactors,意图-事实链+共享黑板,TCH全54题唯一) | github.com/chainreactors,wiki.chainreactors.red;候选项目=Cairn AI;**待克隆深析** |
| 燕巡(北大,数十专项agent并行,闭环验证零误报) | 商业闭源,白皮书/公开材料待研 |
| Artex Pro 企业版 | 闭源不可得(描述=开源+安全管控,我们账本执法已同向更硬) |
## 活体服务
GraphLed webui 8900(口令在启动日志/TANYIN_OPERATOR_KEY)·ARTEX 8787(ARTEX/Whg1995!,JWT)·CSAI 8443(admin/Whg1995!,自签)·ZhuLong 靶场3081+7090/控制台远端1995·测试禁占口 8900/3000/8787/8443
## 凭据律: 上表口令仅限本地开发,永不入报告/入库

## 第六参考入库(2026-10-19)
| 仓 | 路径 | 要点 |
|---|---|---|
| cyber-harness(=衍迹进化体,原aiscan) | .research/repos/cyber-harness | 18M/1045 Go文件/AGPL;四入口=aiscan(agent扫+代理+IOA)/**cyber-audit(模型主导源码/二进制审计——用户源码审计方向的直接参照)**/cyber-web(会话事件工件Hub)/agent(最小本地agent);**Quick Connect一行命令节点回连分布**;--verify=off 确定性扫与AI验证分离;exts十五件(proxy录音/pty/mcp/otel/ioa) |
| GenCPT | /Users/wgen/Sectest/GenCPT(本机) | 188文件17子技能;chain-builder/chain-verify/adversary-verify/attack-reasoning/cross-ref/evolve;graph-viz=统计栏+Pipeline时间轴chips;49攻击模式/226合规规则 |
| 排期: cyber-harness 逐件对齐舰(E舰)=下一空槽或T6后; 源码审计设计舰消费 cyber-audit 入口 |
