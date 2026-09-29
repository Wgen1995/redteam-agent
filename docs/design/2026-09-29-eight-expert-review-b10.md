# 八视角专家评审发现台账（批次 10 输入）

- 日期：2026-09-29　评审对象：TanYin 实现+测试+三轮战（G-r4）调测效果
- 评审编制：8 路独立后台子代理（安全测试/渗透/蓝军/软件工程/架构/文档一致性/自动化/AI-agent），全程只读，证据=文件+行级
- 本轮已修（P0/P1）见 HANDOFF 对应节；本文件=未修项分诊清单

## P2（批次 10 修）

| # | 域 | 发现 | 证据锚 | 修法 |
|---|---|---|---|---|
| 1 | 评估效度 | 响应体 GT marker=零摩擦紫队信标：34 检出中 28 枚（82%）凭路径枚举+静态文案命中，recall 度量路径字典召回非漏洞利用确认 | 蓝军专家；svc-shop/app.py:26 等 15 枚漏洞参数服务端不读 | 检出主通道改参数依赖行为差分（payload 差异错误/时延/OOB 回连——复用 tanyin-canary）；双轨公布 beacon 召回/行为差分召回 |
| 2 | 误报分类 | CORS-01（ACAO:*+credentials）真实环境不可利用（浏览器拒收通配源凭据）；CSRF 两靶无会话前提=CWE-306 伪标签 | 蓝军专家；本轮已去 credentials 头（组合失真修复），类目重标待做 | CSRF 改 POST+会话形或重标 broken-access-control；GT 类目口径更新 |
| 3 | 靶面写实 | svc-login 限流=类级全局计数器跨端点串扰（一端连击另一端出 marker；重放非自包含） | 渗透专家；app.py:24,29,49 | 计数器改 per-(path,method)；EV 卡增「重放前置序列」字段 |
| 4 | 靶面写实 | POST 体 EV 重放 3/3 失真（tanyin-replay body 传递丢失→400/403；RATE-01 reproduced=残留计数器假象） | 渗透专家；replay/EV-r4-0020|0029|0030/1.json | 重放器 parse_raw_request 后打印 body 长度自检；修 body 传递；RUNBOOK P4 增自包含性口径 |
| 5 | 证据完整性 | E-index 工件哈希 34/34=sha256(空串)（touch 空文件 SOP 化=缝⑧34 倍放大）；excerpt 列拼贴损形 | 渗透/swe 专家；E-index 双哈希列 | add-evidence 用卡片 raw_request 回填 .raw 真身；excerpt 加机械形校验；简报删 touch 指引 |
| 6 | 评估键形 | v3 同键碰撞 2 组（login 双条/charges 双条）单 finding 双 marker 可双计分；hauth 组跨实例蹭分 | sec-test/doc 专家（独立复核一致） | v4：同键多 GT 条强制一 finding 至多计一；路径尾段数字化归一同步 |
| 7 | 指标面 | recall-only 无 precision/噪声面；M09 基线三重过时（id/title=authz、desc 种 20、baseline=1.0 冻结；CI 绿靠 ENV-SKIP） | sec-test/automation 专家；metrics-v1.json:142-155 | 以 G-r4 精度门后 0.56 重定标；并报 precision 代理指标 |
| 8 | 架构执法 | scope matcher（后缀/CIDR）与键形 v3 脱节：G-r4 全部 41 目标资产误判 out_of_scope→34 findings 挤单一无绑定 intent | 架构专家；write_cmds.py:144-161,689-701 | matcher 支持 svc-* 服务名形（或 scope 显式列名）；add-finding 增 scope_check↔assets.in_scope 联查 |
| 9 | 架构单源 | 五工具各自复制 append_tl+EPOCH 缺省（guard/canary/budgetctl/replay/egress）；resume-kit 缺省取末行或倒退 56 年 | 架构专家；tanyin-{guard:32,canary:63,budgetctl:35,replay:80,egress:25} | timeline 铸造收拢 ledger 单源写函数；废 EPOCH 缺省 |
| 10 | 契约链 | shared/LEDGER.md 名存实亡（12 处悬空引用）；02a 仍带 -draft 后缀；签名三源并存 | 架构专家；contracts/02a、selfcheck.py:33 | 02a 升格正名或实体化 shared/LEDGER.md；KNOWN_COMMANDS 派生化 |
| 11 | 可重复性 | 三轮战具全活 /tmp（~90 脚本跨战互引）macOS 清理即灭失；G-r4 完整会话未入库无 CI 金样钉 | automation 专家；本轮已归仓 battle-kit 三模板 | G-r4 消毒后收编 tests/fixtures/ 金样会话；CI 钉双轨 recall |
| 12 | CI 覆盖 | E0 selfcheck --static 不在 ci.yml；RUNBOOK §2 无 teardown 行（忘 down=internal 网零症状占死子网） | automation 专家；ci.yml:18-50 | ci.yml 增 selfcheck 步+RUNBOOK S16 teardown+就绪探测 |
| 13 | 文档漂移 | RUNBOOK §6 判定门与命令不符（无 --baseline 默认 0.85）；dict-v2 §四类目口径未同步；HANDOFF 9→18 测数无从对账；22 类 vs 实 23 类措辞 | doc-consistency/swe 专家 | §6 显式 --baseline；§四补勘误；HANDOFF 补勘误行 |
| 14 | 知识飞轮 | 战记归因未核即入册（userenum「被计数文本淹没」与种子不符；JWT-01 归因当时未核种子缺陷）→PR-0005 已带错喂养 | 渗透专家；本轮 RT-0001 勘误页在途 | register 流程增归因抽样核验步（honest_misses 逐条对 seed 可达性复核） |
| 15 | 对照口径 | 「独立战士 2.1 倍反超」=分母置换+知识继承+子集不可比三重混杂；同子集真对比=17/20(0.85) vs 14/20(0.70)=+21% | ai-agent 专家；本轮 HANDOFF 已勘误 | 战报一律同子集口径；独立性分层声明（行为面 vs 键形对齐面） |
| 16 | G-51 沉淀 | 「interrupt 破局律」仅单源散文无投递时序工件；GT 零读无技术凭证（仅旁证） | ai-agent 专家 | 四轮战落 send_message 时序摘录入交战区；战士留存读取路径自报清单 |

## P3（记录，择机）

- docs/design/ 91.5% 被 vendored 三仓占据（imported/ 290 件）→迁 .research/（架构专家）
- repro_command「第三方可跑」零机械校验+G-r4 已沉淀拼贴损形（架构专家）
- knowledge.py 1322 行 god-module 十族混居→拆包 facade（swe 专家）；lint() 137 行单体拆 _lint_k1/_k3/_freshness
- VOCAB 缺失静默吞 OSError→KnowledgeEnvError 两态分流；坏 last_verified 出 WARN（swe 专家）
- GT 键形 RUNBOOK 向战士披露稀释独立性→键形归一全收 scorer（sec-test 专家）
- replay suggest 回显 /tmp/G-r4 错路径（sec-test 专家）
- G-r4 timeline 门禁段字面量倒挂（17:30 早于 17:00 行）；scope 注记 out_of_scope 叙事洞（并入 #8 修）
- TestCli 手工 Base 实例化→mixin 化；877 测串行无声明式分层→三层固化脚本/CI 矩阵（swe 专家）
- 基础镜像无 digest 钉；tools.lock 对 compose build 面射程外（automation 专家）
- 靶面类分布近均匀全 web 类、防御摩擦≈0→噪声 IPS 服务+认证类加权+端口异构（蓝军专家）

## 强项共识（八专家各自独立指出）
- 反自欺编制有效：G-50 独立战士对照+逐 miss 归因+诚实 FAIL 门保留（蓝军/渗透/sec-test）
- 战创→回归闭环真实落地：每轮实战缺陷当轮 TDD 钉死四处同步（swe/arch/doc）
- 键形 v3 收口=检出/评分分离架构红利：不读答案的执行体测出了评分器 bug（ai-agent/sec-test）
- eval docker 耦合已解耦到纯函数边界，G-g1 夹具模式可直接推广战果金样（automation）
- 契约体系可机械自证（自验节+微版本勘误流水+Tier0 单点硬门）（arch）
