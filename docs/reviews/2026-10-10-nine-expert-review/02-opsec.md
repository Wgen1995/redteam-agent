# 02 红队/实战对抗专家（OPSEC）深度分析（2026-10-10 九维专家会诊）

## 现状强项
1. 凭据生命周期同类罕见完整：vault PBKDF2+EtM（tanyin-guard:80-111）；账本只见 {{vault:cred-N}} 占位；guard 双向真值替换脱敏长值优先；密值禁 argv 走 env/stdin；inject 过 permitted_actions 门。
2. 四层执法纵深+策略单源：Tier0 scope→Tier1 guard→Tier2 hooks→Tier3 egress.acl；deny/scope 单源 enforce.py；egress default deny+exclude 优先+DNS pin+OOB+canary 段（canary 命中=告警放行留痕——"阻断反掩盖触达事实"设计意识好）。
3. 自检式执法金丝雀真跑：RFC5737 诱饵 tier0-3 逐层探测、三形态须全拦才 blocked、无响应=fail-closed；battle-25 实证 5/5 blocked 落账。
4. P6.0 清理门副作用可逆一等公民：revert_cmd 列；request:* 强制 --revert-cmd 否则 REJECT；irreversible 逐条审批；cleanup 逆序核销。
5. 供应链锁定：tools.lock ECDSA 验签+templates.lock sha256+运行时 nuclei digest 比对。

## 关键缺口
1. 【最严重】OPSEC 完全缺席执法层：九门无一条 OPSEC 条款；UA 自报家门（tanyin/1、probe/1.2、tanyin-replay/1——一条 IDS 规则全量归因）；nuclei 无 -rl/-etags；budgetctl rate 滑窗熔断代码存在（tanyin-budgetctl:121-150）但未接 gate_chain 且 rate_limit 字段空——真实战从未启用；授权窗只在 P5 lint 查、guard exec 不查墙钟。作者 VOL-09B:595 自己写的"预算必须是代码不是话术"恰是现状。
2. Tier2/3 纸面纵深：opencode.json 是 bash {"*":"allow"}；Tier2 hook 模板从未挂载；battle-25 零 egress-deny 事件——流量根本没过代理；一切界外防线=SKILL 一句指令，子代理漂移直接 curl 即绕。
3. 打穿别打塌只覆盖删库级：DENYLIST 24 模式全是毁灭单命令，无 DoS 工具/激进档/BENCHMARK 型；无并发上限；guard 孙进程不 reap；request-ticket 只记 cmd[0]+argc——full argv 不落账，流量画像不可重建。
4. 金丝雀=防自伤非防蜜罐，反蜜罐能力零：执法 canary 是本地模拟（自明不发包）；recon canary 思路新但 battle-25 [canary] 段空未部署；无蜜罐指纹启发式——踩中客户蜜罐当场标死无护栏。
5. 凭据落地：vault/.key 明文与 enc 同盘；TY_CRED_SECRET 环境注入 /proc 可读；INFRA 白名单含 pypi/npm/github 未收口。
6. P6.0 痕迹管理边界要诚实：只核销账本登记过的写操作；目标侧日志天然不可逆；是交付卫生不是反取证——文档未区分。

## 可执行建议
| 建议 | 收益 | 量 |
|---|---|---|
| budgetctl rate 接入 gate_chain+P0 八问⑥必填 | 速率上限从查询面变执法面 | S |
| UA/流量画像治理（EV 卡加 ua 字段+禁自名 UA+replay --ua） | 消除单规则归因 | M |
| DENYLIST v2+nuclei 固化 -rl 50 -etags dos,intrusive+孙进程 reap | DoS 风险机械受控 | S-M |
| Tier2 真挂载+egress serve 常驻进 RUNBOOK | 越界防线从 LLM 纪律升宿主机制 | M |
| request-ticket 落 full argv（tokenize 脱敏） | 账本配得上唯一真源 | S |
| vault 主钥不落盘（Keychain/passphrase） | 防主机失陷全解 | S-M |
| recon canary 升级踩蜜罐警报（honeypot-suspect fact） | 已有度量变实战护栏 | M |

## 对标
Threatswarm（OPSEC defaults）正好倒挂；Caldera visibility 可作第五维预算；CS/Sliver malleable C2 流量可塑是纯减分项；Thinkst Canary 对抗——recon-decoys 是正向创新但攻击侧蜜罐识别为零。

## 总评
把自己管得极严（scope 单源/vault/哈希链/清理门/供应链验签皆单人顶级）、却不知道自己有多显眼（UA 自报家门/无限速/Tier2-3 未实挂/零蜜罐感知）的红队系统——内功九段，外功一段，上真实交战第一小时就会被蓝队写进告警看板。
