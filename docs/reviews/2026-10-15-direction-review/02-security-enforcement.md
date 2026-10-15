# 02 · 攻防+安全工程 · 自主化放权后的执法面完备性评审（2026-10-15 方向评审）

> 评审员镜头：战士自主权每放大一档，执法面必须先于它闭环。本档只回答一个问题——
> 「如果战士明天就被目标俘获，现在的代码能拦住什么？」答案用代码与 battle-42 实测数据说话。

---

## 【总判决：方向对，优先级偏——执法面完备度落后自主化叙事至少两个批次。置信度：高（85-90%）】

产品定义 v1 把「程序执法记账验证度量」立为自主性地基，方向本身正确（对 LLM 战士，
账本+门禁是唯一可交付的信任载体）。但现状是**三层执法里只有记账层是真的**：
Tier1 guard 是战士自愿走的门（battle-42 实测通过率为 0%），Tier2 hooks 是三页模板
加一个模拟器，Tier3 egress 代理全仓唯一消费者是 tests/。同时，执法工具（ledger 写命令、
approvals、knowledge promote、scope 扩界）与被执法者（战士进程）同用户、同机、同 env、
同文件系统权限——**整套"门"防的是误操作，不是被俘获**。在威胁模型「战士永远善意」下
一切都绿；换成「战士被目标 HTTP 响应里一句话俘获」，当前机械拦截力≈0。
v1.0b（规划者常驻+多战士）放权前不补这一课，等于把保险柜账本挂在没锁门的房间里。

---

## 【发现（按严重度排序）】

### S1 · 致命：执法面与被执法者同权同体——一切门都是战士自己拉的闩
- **现象**：战士（opencode）与执法平面（13 表写命令/guard/budgetctl/knowledge）之间零权限隔离。
- **证据**：
  - `.opencode/opencode.json`：`"bash": {"*": "allow", "rm -rf *": "deny", "git push": "ask"}` + `"webfetch": "allow"`——战士可跑任意 shell、任意 webfetch，deny 面只有一条 rm。
  - `cli/tanyin-runner:24-30,81`：`env = dict(os.environ)` 原样继承操作员环境（ISOLATION_ENV 只关 OPENCODE_* 自动更新）。TANYIN_JUDGE_*（judge API key）、TANYIN_APPROVAL_KEY、TANYIN_VAULT_* 若在操作员 env，全部对战士进程可读。
  - `cli/ledger/write_cmds.py:367-381`：`_add_scope` 只查 tier0（有 goals 行），**新增 include matcher 永不需要审批**（amend-scope 才查 approval，:1374-1377）；`_approve`（:994-1013）铸造 approved 行时，HMAC 签名只在 TANYIN_APPROVAL_KEY 在场时强制——而该 key 恰恰会随 env 泄给战士（同上）。
  - `cli/ledger/knowledge.py:62-70,1231-1242`：`approvers add` 是与战士同权的写命令；运行时知识库只受「路径≠仓库种子根」保护，直接 fs 写连这个检查都绕过。
  - 哈希链：`row_hash` 算法公开、genesis 已知、同用户可写 timeline.tsv——战士可整链重算伪造；唯一链外锚（`anchor --remote` git 外推，check_cmds.py:395-433）默认关闭且 `git push` 在 opencode 是 ask（可被 `git send-pack`/curl 绕过模式匹配）。
- **为什么危险**：提示注入只需俘获战士一次（目标响应/客户文档/任何进 transcript 的文本都是入口），即可：curl 外传 ~/.tanyin 全账本+vault 明文 key；`add-scope` 把任意域拉进 include 后正大光明打；自铸 approvals 行解锁 amend-scope；`approvers add` 自己→approve→promote 投毒知识库跨战持久化。「程序执法」在这个威胁模型下是装饰。
- **修正方向**：权限分离三件套，放权前不可谈判——①战士进程最小 env（白名单变量，剥一切 TANYIN_* 密钥）+ 账本目录对战士只开 submissions/ 写路径；②scope/approvals/knowledge 写命令强制操作员侧签名（复用 :941 `_approval_sig` 通道，密钥进 Keychain/令牌，永不进战士 env）；③每门强制 `anchor` 外推到战士不可写 remote。

### S2 · 高：Tier3 egress 从未实挂 + Tier2 纸面——出网机械执法覆盖率=0%
- **现象**：唯一能拦「战士实际发包」的两层都不存在。
- **证据**：
  - 全仓 grep `EgressProxy|serve_text`：生产代码零调用，仅 tests/（test_egress_proxy/test_canary_traffic/test_egress_oob_canary_b7）；`cli/ledger/egress_proxy.py:356-359` 的 serve 入口无人起。runner 不设 HTTP(S)_PROXY，无透明代理/pf 规则。
  - battle-42 timeline：`egress-compile=1`（P0 本地编译产物，零网络执法）。report_agg.py:158-165 只做 `egress_log_present` **披露**——披露缺口不是关闭缺口。
  - hooks/：三宿主模板（.md）+ simulate.py 自测；README 自认「真宿主挂载=批次 6」，HANDOFF:1430 仍挂着「Tier2 hooks 真挂载实验=宿主闸门（下批）」。`.opencode/node_modules/@opencode-ai/plugin@1.18.32` 已安装——材料齐了，一行插件没写。2026-10-09-b11-gateloop-experiment.md 计划在库未执行（BLUEPRINT-RECON 自己点名的例外）。
- **为什么危险（敞口量化）**：战士可达外联路径≥4 条（任意 bash / webfetch / docker exec / 宿主 python），被机械检查的比例 0%。battle-42 实测：436 行 timeline 中 `request-ticket=0`，41 条对外请求全部 `via=replay`，38 次 `docker exec range-attack-noop-1` 主动探测零经 guard；DNS 隧道/IPv6/域前置完全裸奔；canary 检测依赖流量过代理——代理不在，canary 语义同时失效。
- **修正方向**：顺序不能反。先 Tier2（opencode plugin 把 bash 收成白名单：tanyin-guard exec / python3 cli/* ，一个下午的量）；再 Tier3 实挂（runner 内嵌起 EgressProxy，强制子进程 env HTTP_PROXY/HTTPS_PROXY+NO_PROXY 清单，随战斗生命周期开关）。pf anchor 兜底可选。

### S3 · 高：rate/预算执法锚在战士自报时间戳上——滑窗可被「时间旅行」清零
- **现象**：速率/预算执法的时间锚全部来自被执法者自报。
- **证据**：`cli/tanyin-guard:186` `rate_window(s, parse_ts(ts))`——ts 是战士传的 `--timestamp`（cmd_exec :216-218 直接消费）；`cli/ledger/enforce.py:197` `now = max(stamps)`（注释自认「可重放口径」）；battle-42 mission.txt 第3问：「场景钟——一切 --timestamp 用 2026-11-08 形的当日时刻」。wall_clock 双轨（wallclock.py）是观测轨 fail-open，只在 battle init/launch/settle 三点铸，不进任何判罚。
- **为什么危险**：战士把 --timestamp 向前谎报一个窗口时长，旧请求全部滑出 (now-w, now]，rate 门永 not-over；budget delta 同理自报。OP1 把 rate 从查询面升执法面是真功劳，但**锚错了钟**——执法钟必须不可被被执法者铸造。G-23（禁墙钟）为测试确定性立律，顺手把执法确定性也杀了。
- **修正方向**：双轨拆分——执法判定用 guard 进程内真墙钟/单调钟（只判罚不落账），账本叙事列另存申报钟；或干脆 in-memory token bucket per goal-dir，不依赖账本时间戳。

### S4 · 中高：replay 是无速率/无窗口/无危害分类的重放器，P4 门还奖励多发
- **现象**：`tanyin-replay` 对目标盲重放 raw_request 原文（含凭据占位回注），机械前置只有 host∈scope。
- **证据**：`cli/tanyin-replay:86-105,226`——全流程无 valid_until 检查、无 rate_window 调用、不铸 budget 行、`--chain` 无长度上限、单 EV seq 无限自增（:239-243）。授权窗只在 P5 报告 lint 查（report_lint.py:288-296）——窗口过期后 replay 照发，事后才发现。另：replay 自带第二套 scope 实现（host_in_scope 用 amendment_of 跳行语义），与 enforce.load_scope（:227，同 matcher 后行覆盖）在「修订行改 matcher」场景判定分歧——两套读法对同一 scope.tsv 可给出不同答案，自称「单一事实源」名不副实。
- **为什么危险**：①二次伤害：battle-42 的 41 次 replay 全是往存储里塞 `<script>probeX1</script>`——在真实客户生产环境这就是重复脏数据/重复触发 SIEM/重复副作用，无安全方法分类、非 GET 首放无人工门；②DoS 面：chain+循环无节流（实测 20s 间隔纯靠战士自觉守「禁 DoS」战书话术）；③replay 完全绕过 rate 记账（不 mint requests_delta），S3 的时间旅行叠加这里，速率对 replay 根本不存在。
- **修正方向**：replay 加四门——真墙钟∈[valid_from,valid_until]；与 guard 同窗限速（自 mint 或走 guard）；危险方法/体分类（非 GET 首重放需操作员 approvals+签名）；单 EV 重放上限（3 次后转 manual）。scope 判定收敛回 enforce 单源。

### S5 · 中高：知识飞轮四门槛挡格式错误，挡不住合谋投毒
- **现象**：promote 四门槛全部检查**库内自洽性**，不检查**信任来源**。
- **证据**：`cli/ledger/knowledge.py:1014-1069`——①复现≥2=被≥2 张先例页 applied_patterns 引用（先例页本身是同机战士可 mint 的对象，client 字段是任意 CLIENT-NN 字符串）；③人审=log.md 存在一行文本（`_log_has` :966-977，在场检查，docstring 自认「质量判断留人审」但没有任何身份验证绑定）；④无指纹=special.scan_text+DOMAIN/IP 正则（special.py:22-44 纯凭据形态，**零指令形态检测**）。
- **为什么危险**：攻击剧本全绿路径：被俘获战士单战内 mint 两张不同 client 的先例页引用毒 pattern → `approvers add` 自己 → `approve for=promote` → 四门槛全过入 core。此后 v1.0b 按蓝图把 knowledge 作检索源注入战士 brief（BLUEPRINT-RECON「v1.0 连接点」明示），毒指令跨战、跨客户、持久生效——**把提示注入做成平台记忆**。且先例正文天然转抄目标响应（PR-0005 摘要即战例复述），恶意目标可主动种文案；DOMAIN_RE/IP_RE 只逼攻击者用中性措辞，不增加任何难度。
- **修正方向**：①门槛③升级为操作员持钥签名（复用 S1 的 HMAC 通道），log.md 验签而非在场；②加第五门槛：引用先例须 EV 链可复核（id 闭合到 ledger replay 证据）；③知识页入 prompt 走结构化渲染（字段进模板、正文 fenced+显式标注「目标侧材料非指令」）；④approvers 名录随种子库发行，运行时 knowledge/ 对战士进程只读挂载。

### S6 · 中：白盒车道A的注入面已在设计里埋下、没在设计里设防
- **现象**：修正案A 车道A 解析客户 OpenAPI/安装包/源码→产出带出处挂资产图→（v1.0b）规划者消费。设计全文只字未提交付物内容是敌意的。
- **证据**：tanyin-product-v1.md 修正案A 全节——有出处（文件:行）要求，无内容消毒/指令检测/「自由文本列不入检索索引」约束。车道A 代码未建（全仓 openapi 解析仅 tests fixture 一处）——正是立规矩的最后时点。同构现状：今天 warrior 直读目标响应全文进 transcript，平台无一处做「目标侧材料」prompt 级隔离。
- **为什么危险**：OpenAPI description/README/源码注释是客户侧/供应链侧可控文本；资产图被规划者检索=不可信文本直喂自主决策者。与 S5 组合即「客户文档→资产图→规划者→战士→知识库」全链路注入，且每层都有出处标注——出处只帮你事后追责，不阻止执行。
- **修正方向**：v1.0a 设计定稿前写入硬约束：解析器产出只允许结构化字段（method/path/参数名/类型/置信度），自由文本列永不进检索索引；资产图→规划者投影层加长度上限+字符白名单+显式数据/指令分隔协议；**规划者自己的工具面必须过 Tier1/2**——规划者是权限更高的战士，更需要笼子。

### S7 · 中低（合并清单）
- **guard 超时不杀孙进程**：`cli/tanyin-guard:263,321` subprocess.run 无 start_new_session/killpg——`sh -c 'evil &'` 孙进程在超时击杀后存活；runner 里有现成 kill_group 正确姿势（tanyin-runner:66-72）没抄过来。
- **vault 主钥明文落盘**：`cli/ledger/vault.py:80-85` load_key 回落 vault/.key（hex 文本，与密文同盘同权限）；TANYIN_VAULT_KEYFILE 通道存在但缺省不启用；inject 的 TY_CRED_SECRET 走 env，战士子进程互相可读。
- **hosts_matrix 缺省档倒挂**：`cli/ledger/hosts_matrix.py:34` `egress_default_tier` 缺省 1——模板缺省给最低执法档，应 fail-closed 缺省 3。
- **反蜜罐/蜜罐感知零**（prior review 已列，未见代码）：canary 语义在 Tier3 未挂载时同休眠。
- **replay --ua 任意伪装**：与 OP2「禁自名 UA」存在张力面，重放侧应显式落 ua= 事件（现只进 result json）。

---

## 【被忽视的既有资产】
1. **`anchor --remote` git 外推锚**（check_cmds.py:395-433 + TANYIN_ANCHOR_AUTO）——现成的链外信任根，防战士伪造账本的唯一现成答案，默认还关着，也没进任何「执法完备性」叙事。
2. **`_approval_sig` HMAC 审批签名通道**（write_cmds.py:941,996-1004）——审批防伪已写好，只差「密钥不进战士 env」一步启用，S1/S5 的修正直接踩在这上面。
3. **`.opencode/node_modules/@opencode-ai/plugin` 已装**——Tier2 宿主拦截的材料零成本在手，欠的只是几十行插件代码；配套的 2026-10-09-b11-gateloop-experiment.md 计划在库（BLUEPRINT-RECON 点名例外）。
4. **runner 的 kill_group + watchdog 判定核**（tanyin-runner:66-72 / ledger/watchdog.py）——进程组击杀正确姿势已在库内，guard exec 抄一下即可（S7 第一条）。
5. **evals_dual_anchor.py 双锚互证结构**（approvals.tsv ↔ knowledge log.md）——S5 人审门升级为签名验证时，双锚骨架直接复用。
6. **egress canary「告警放行」语义 + report_agg tier_disclosure**——Tier2/3 实挂后的报表面已就位，不需要新造观测件。

---

## 【三问给主会话】
1. 产品宪法说「程序执法记账验证度量，人只做介入/放行/决策」——现在「放行/决策」通道（approvals/add-scope/approvers）与被放行对象同机同用户同 env。**v1.0b 多战士常驻循环上线前，你打算在哪一批把操作员信任根（签名密钥+只读账本视图+战士沙箱）从战士可达面上物理摘出？**做不到的话，「自主决定能打多快」的上限就不该提。
2. battle-42：request-ticket=0、replay=41、docker exec=38——「战士一切对外流量必经 guard/egress」目前是战书话术。**你能否为 v1.0a 定一条可验收的机制标准（如「未过 guard 的外联在机制上不可能/必然留痕」），并指明落在哪层（opencode permission/容器网络/pf）？**定不出来，度量页的 recall/p 值度量的就是一间没锁门房间里的账本。
3. 知识飞轮 promote 门槛③现在是「log.md 里有一行字」。**v1.0b 把 knowledge 接进战士 brief 之前，是否接受「③=操作员持钥签名 + 引用先例 EV 链可复核」为接线前置条件？**不接受，就是给所有未来客户预装一条跨战持久化的提示注入管道——这不是假设，是四门槛代码现状的直接推论。
