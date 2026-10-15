# v0.9.6 执法面升权批 Plan（E2 S1-S5,冻结于「开」）
依据: docs/reviews/2026-10-15-direction-review/02-security-enforcement.md + direction-amendment-1.md 票②。
## SEC-1 舰（S1+S3+S5）
1. S1 信任根摘出: 战士进程 env 白名单化（继承面仅 PATH/HOME 等必需;TANYIN_JUDGE_*/APPROVAL_KEY/密钥类全剥离——grep 全部 TANYIN_* 注入点逐一过白名单）;approvals/approvers 两账对战士降只读（guard 层拦截写命令）;审批启用 _approval_sig HMAC 通道（现成件接一步: 密钥 env 仅操作员侧,签名进账本行,验签测试）。
2. S3 执法钟防时间旅行: enforce 限速/预算窗的时钟锚改为账本 seq 单调+链上时间戳（自报 --timestamp 降参考;战斗内回拨/前跳>阈值=REJECT 上账）。
3. S5 promote 签名门: tanyin-knowledge promote/approve 增持钥签名（操作员密钥 env,不进战士面）;无签名行 lint 拒;EV 链复核钩子（复核记录可链上验证）。
## SEC-2 舰（S2+S4）
4. S2 egress 实挂: runner 出网命令机械过 egress 决策（docker exec/外联工具走 decide 四态,request-ticket 自动记账——覆盖率 0%→机械强制）;安装/自检步骤文档化但不动 ZhuLong。
5. S4 replay 授权窗+治理: 授权时间窗检查+危险方法分类（非 GET 默认拒,--allow-method 显式开）+次数帽+scope 判定吃 enforce.load_scope 单源（删第二套实现）。
## 白名单
SEC-1: cli/ledger/{enforce,wallclock,knowledge*.py,approvals*}.py、cli/tanyin-guard、runner 注入点文件（grep 后实报）、tests/*。SEC-2: cli/tanyin-egress、cli/tanyin-replay、cli/ledger/egress*.py、runner 执行路径、tests/*。**两舰白名单互斥;都禁碰 cli/webui/ 与 static（收口舰作业区）**。
## 验收
TDD 红绿+全量零破坏+battle-42 真账本冒烟（时戳回拨被拒/env 白名单生效/promote 无签名被拒/replay 非 GET 被拒四实证）。
