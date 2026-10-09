# 06 安全审计专家（证据链与合规）深度分析（2026-10-10 九维专家会诊）

## 现状强项
1. 证据卡双指纹+机械重放+防改判三道锁：raw/norm 双 sha256；tanyin-replay 真机械判定（vault 进程内解密→scope→实发→matcher 三态）；set-replay-state 拒「not-reproduced 后直接 VERIFIED」；评分器再复设防线。battle-25 实测 36 条 replay-probe 可对勘。
2. 评分器精度门超过一般自评水准：无 VERIFIED 零分/not-reproduced 拖累/反膨胀/词证差分双轨/post_auth 须链。关键：beacon 不是塞词就过——marker 须在 EV 卡 matcher 且重放真实发包响应含词。
3. 授权完整性门有真比对且实战诚实 halt 过：report_lint 三查（授权书实测 sha vs 声明、签发 ts∈窗口、approvals 行）；battle-25 实证 sha 不符→gate-blocked「不伪造 halt 待人工」——自证诚实纪律无监督下真实生效。
4. 防撕裂/防失控工程密度高：原子写/TSV 转义律/vault EtM/保留词表/restart 六护栏+孤儿对账；复盘飞轮真裁真决。

## 关键缺口
1. 【最高危】哈希链无密钥无外部锚定——「防篡改」实为「防意外」：row_hash=裸 sha256，verify_chain 只从文件自身重算——改 TSV+重算全链全绿；保留词只挡命令面，直接写文件可伪造任意 gate-exit。README「全程账本留痕防篡改」名不副实。业界：HMAC 链+周期链头外锚（RFC3161/git remote——sessions 入 git 客户持 remote 重写历史会被 push 拒绝）。
2. 时间戳全链自报（场景钟）对真实交付致命：一切 ts 由 AI 提供+「禁 datetime.now 进产物」明文纪律；battle-25 930 行全虚构日期。账本无法向第三方证明事件何时发生；授权窗比对是对自报钟自证。业界：PCI 取证可信时间源/法庭可验证时间戳。
3. 审批链无身份认证：approver 自由字符串+command_hash 只验格式；--verify-signoff 只查「存在 approved 行」——AI 可自落审批行冒充客户（battle-25 的 approver 就是任务书转写）。人写的行与 AI 写的行密码学不可区分。业界：签名审批/带外确认/持钥 HMAC。
4. P4 fresh 盲重放是提示词约定非机制；matcher 同写者 authored；重放覆盖不阻断出 P4（replay-summary 只查任一 EV 重放——RT-0023 实证 54/32 照样过门）。
5. 报告自证自验缺第三方可执行验收路径（sign_gate 14 道门超 OSCP 模板但全由同一套 CLI 自评）。
6. vault 密钥与账本同盘（防失控 AI 够用，防取证不足）。

## 可执行建议
| 建议 | 收益 | 量 |
|---|---|---|
| 链头外部锚定：每门 exit git commit+push 客户可见 remote | 无声改账须重写已推送历史 | S |
| approve 持钥通道（TANYIN_APPROVAL_KEY 派生 HMAC 签 command_hash） | P5.5 从自报变持钥者在案 | S |
| 时间戳双轨（保留参数 ts+每行 CLI 自填 wall_clock 入哈希，报告用墙钟） | 「何时测」可辩护 | M |
| HMAC 链可选双轨（TANYIN_CHAIN_KEY 在位则 HMAC） | 失控 AI 造不出合法链 | M |
| replay-summary 收紧（全部 evidence_ids 须终态+覆盖率阈值） | 堵 54/32 洞 | S |
| add-goal 授权校验前移（文件在位+实测 sha 一致才收行） | 不再靠 LLM 诚实兜底 | S |

## 对标
OSCP（证据卡结构超过 screenshot+steps 但缺人工复核背书——机器验证强人的担责弱）；PCI DSS Req.10（三核心：日志不可改/时间可信/定期外发——全缺但双指纹已达防意外级）；等保 2.0（13 表远强 Word 底稿但签字链要实体身份）；Cobalt Strike（链深度超 CS 但相当于 SIEM 未外发状态）。

## 总评
把「AI 自证诚实」工程化到业界罕见深度（重放门/双指纹/反改判/诚实 halt 实战在案），但整条证据链仍是单写者自报自验——无密钥无锚定无可信时钟无身份凭证；对内防失控已够，对外抗辩（法庭/监管/客户抵赖授权）还差三件套：HMAC+外部锚定、可信时间、持钥审批。
