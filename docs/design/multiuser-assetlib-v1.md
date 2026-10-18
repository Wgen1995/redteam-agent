# 多用户与资产库 v1 设计稿 —— 本地账户四角色 + 双签复核 + 安装级资产真值域（multiuser-assetlib-v1）

> 设计舰出品 · 2026-10-19 · 零代码实施（本稿只设计不动工）。
> 缘起（用户令）: 「很多人登录使用开展渗透」+「ARTEX 资产库」——单操作员口令进不了团队门（很多人无法同时登录作业），任务资产各自为战、无跨任务真值域与复用。
> 定位律: 渗透主航线零改动——本稿只做两件事: ①把「人面」从 1 人扩到 N 人（人=读+审批+建任务）; ②把「资产」从任务内账本升为安装级真值域（跨任务登记/授权复判复用/导入合并/覆盖历史）。三条铁律零改动: **单仗单写者、账本哈希链、CLI 单源写路径（webui 零账本直写）**。
> 前置继承（不推翻任何在册裁决）: W7「三角色RBAC+双人复核」（蓝图:28）; C 舰 Z8（对齐 ZhuLong 用户管理地板+超点=审批-执行分钥+approver 入哈希链）; A 舰 B26/B33/B42/B43（资产拦截七种匹配/资产页/DSL/外部同步）; 06-whitebox-dualgraph:50（跨战资产真值域=快照导入+链头锚定裁决）; source-audit-v1 §三（安装级 registry 不进 13 战表先例）; O7（SQLite 投影层升格必做, graphled-architecture-v1:41-44）; 报告双签先例（api_v2_reports.py:28-29「两把互异 approver=双签就绪」）; 任务生命周期 SIGNED=双签（task-lifecycle-v1:8）。

## 〇 输入实读清单（六项必读, 全部实读, 只读零写）

| # | 输入 | 实读证据 | 形态一句话 |
|---|---|---|---|
| ① | B 舰 CSAI 对齐档（docs/reviews/2026-10-18-realign/B-csai-全件对齐.md） | D1/F4 行全文+手册:180-181+rbac.md:49-52 引文 | RBAC 四档=viewer 23/auditor 24/operator 50/admin 72 权限+资源范围显式授权+变更留痕; rbac-guards=全局函数包装 400 余写函数不改业务码加权限门; 我方在册判=**72 粒度不追全量**（初表:29 取舍）, 超点=审批-执行分钥+approver 入哈希链 |
| ② | A 舰 ARTEX 对齐档（…/A-artex-全件对齐.md） | B26/B33/B42/B43/D6 行全文 | 资产拦截=任务级七种匹配+白名单语义（手册:241,393-394）→我方 W2 matcher kind 扩（url-exact/domain-fuzzy/ip-fuzzy/cidr, enforce.load_scope 同源）; 资产库=六类卡+DSL 搜索+批量导入+任务间共享（手册:261-262,297-298）; ScopeSentry 同步=项目维度+公司归并→W7 可选适配; 双图=资产图全局+探索图每任务+裸两列 anchor 桥 |
| ③ | ZhuLong 用户管理（平台仓 apps/server, 本地只读零写） | migrations/0001+0006 全文+routes/admin.ts 全文+services/password.ts 全文 | users 表: scrypt(N=16384,r=8,p=1,keylen=64) 只存哈希（串式 `scrypt$N$r$p$salt$hash`）、role(admin/member)+biz_role(operator/auditor)、status(active/disabled/deleted 软删行永存)、created_by RESTRICT; sessions=sha256(256 位随机令牌) 明文不落库+7 天滑动+last_seen; 管理面端点 46-49/63（列表/建/改/重置密码/软删）+自保护三律（不可自降级 400/不可自禁用 403/末管理员保护）+审计全写面 |
| ④ | 单操作员现状（仓内 cli/webui/server.py 实读） | :80-130/:405-500/:890-1060 段 | OPERATOR_KEY 单口令（hmac.compare_digest）+错 5 锁 60s+cookie 8h; 读面门 W1 已闭（302 页/401 API）; APPROVAL_KEY 持钥审批: HMAC 签 sha256(revert_cmd), 钥只进子进程 env; approvals.tsv 7 列, approver=「操作员(观察面)」字面量; timeline actor=「人工」字面量; 写面=subprocess 调 CLI（窄门律） |
| ⑤ | battle_registry（仓内 cli/ledger/battle_registry.py 228 行全文） | docstring+admit/release/claim_ports 段 | 单仗单写者的资源仲裁核: registry.json+flock 互斥 admit/release/set_pid/claim_ports+预算帽仲裁（used+new>cap 数学披露）+保留口 8900/3000/8787/8443+死 pid 自愈回收+损坏册 fail-closed ValueError |
| ⑥ | O7 SQLite 投影（在册裁决） | graphled-architecture-v1:41-44 | 升格必做: schema+确定性重建（坏了删了从账本重建）+资产/覆盖/发现查询读路径迁移 ~700 行+性能回归钉（追加 3400 行/s 基准）; 天花板诚实=上千人同写同一仗才触顶, 触顶日=投影层读写分离、真相层不动 |

> 命名澄清（防同名混物）: 仓内已有 `cli/ledger/authz_matrix.py` 是**被测目标**的 role×endpoint 覆盖投影（吃 creds.tsv 角色, 服务渗透测试的越权面度量）; 本稿的平台 RBAC 是**平台自身**的访问控制——同名不同物, 实施时新模块命名 `rbac.py`（平台面）与之区隔, 文档与代码注释双澄清。

---

## 一 【必答 A】用户体系 = 本地账户 + 四角色 + 读写面矩阵 + argon2id

### 1.1 本地账户（安装级, 不进 13 战表）

位置 `$TANYIN_HOME/users/users.tsv`（缺省 ~/.tanyin; TANYIN_HOME 先例=battles/serve/gt 三处同律）。列（11）:

```
id, username, password_hash, role, status, created_by, created, updated, disabled_at, note, schema_version
```

- username 全局唯一; **软删律**（ZhuLong 同律）: status=active/disabled/deleted 三态, 删除=软删行永存（列表/登录/授权候选全排除）——用户名出现在历史 timeline/approvals 行里永不悬空。
- created_by 记建号管理员 id（首管理员=NULL）——追责血缘。
- 存储纪律: TSV+flock+原子整替换（账本同工艺）; users 目录 0700。

### 1.2 角色 = 观察员/审计员/操作员/管理员 四档

| 角色 | 一句话职责 | 地板对照 |
|---|---|---|
| 观察员 observer | 只看不打: 全读面, 零写面 | CSAI viewer（23 权限档） |
| 审计员 auditor | 复核与终审: 全读面+审计写面（发现三态终审/复测触发/审批签名/报告第二签） | ZhuLong biz_role=auditor / CSAI auditor |
| 操作员 operator | 作业主体: 建任务/点火/指令/范围修订提案/资产登记导入/凭据入库 | ZhuLong biz_role=operator / CSAI operator |
| 管理员 admin | 平台管家: 用户管理+平台参数+全部操作员权 | ZhuLong role=admin / CSAI admin |

判词: **四档对齐 CSAI 同构、词面贴 ZhuLong 中文地板, 不追 72 权限粒度**（在册取舍继承）——我们的权限面收敛为 §1.5 的 15 面×角色集合, 机械表驱动。rbac-guards 的「包装不改业务码」思想吸收为 SURFACE 注册表单源（§1.5）, 但它是函数包装我们是路由面声明, 形态从简。

### 1.3 口令哈希 = argon2id 主格式 + scrypt 兜底（双格式自描述）

- **主格式 argon2id**（m=64MiB, t=3, p=4, 盐 16B 随机, keylen 32）: 串式自描述 `argon2id$v=19$m=65536,t=3,p=4$<b64盐>$<b64哈希>`。
- **兜底格式 scrypt**（stdlib hashlib.scrypt, N=2^14, r=8, p=1, keylen 64）: 串式与 ZhuLong 同形 `scrypt$16384$8$1$<b64盐>$<b64哈希>`——clone 即用零依赖律不破: argon2-cffi 不在场时建号/改密自动落 scrypt, 在场时自动升 argon2id。
- 验证按前缀判别+常数时间比较; **登录升档**: 旧格式（含未来参数过时）验证成功后当场重哈希落新格式（事件入审计链）。
- 登录防爆破: 每用户错 5 锁 60s（沿用现律）+全局按源 IP 失败节流（ZhuLong 同律）; 锁定事件入平台审计链。
- 依赖位呈裁（待裁②, §七）: argon2-cffi 是本仓第一个运行时 pip 依赖——推荐=可选依赖（在场升档、缺席兜底）, 不破 clone 即用。

### 1.4 会话

- cookie `tanyin_sess` 沿用（HttpOnly+SameSite=Strict）; 令牌=256 位随机, 库存 sha256（**明文令牌不落盘**, ZhuLong 同律）。
- `$TANYIN_HOME/users/sessions.tsv`: token_hash, user_id, created, expires_at, last_seen; TTL 8 小时**滑动续期**（活动刷新, 思想同 ZhuLong 7 天滑动、时长贴我们的班次制现值）。
- 会话写=flock+原子替换; 登出=删行+审计事件; 改密/禁用/软删=该用户全会话即失效（ZhuLong 同律）。

### 1.5 读写面矩阵（15 面 × 4 角色——rbac.py 的 SURFACE 注册表, 单源机械执法）

| # | 面（人话名） | 观察员 | 审计员 | 操作员 | 管理员 |
|---|---|---|---|---|---|
| 1 | 全部只读页/API/SSE（总览/任务详情/资产覆盖/攻击链路/实时动态） | ✅ | ✅ | ✅ | ✅ |
| 2 | 证据原文抽屉（raw_request/回显） | ❌（脱敏） | ✅ | ✅ | ✅ |
| 3 | 报告查看与下载 | ❌ | ✅ | ✅ | ✅ |
| 4 | 新建任务+一键执行（点火） | ❌ | ❌ | ✅ | ✅ |
| 5 | 任务控制（暂停/恢复/停止/指令下发） | ❌ | ❌ | ✅ | ✅ |
| 6 | 范围修订提案（amend-scope, maker 侧） | ❌ | ❌ | ✅ | ✅ |
| 7 | 审批签名（checker 侧, 含双签第二签; 高危类第二签须审计员/管理员） | ❌ | ✅ | ✅ | ✅ |
| 8 | 发现终审判定（三态: 确认/存疑/否决） | ❌ | ✅ | ❌ | ✅ |
| 9 | 复测触发（机械重放） | ❌ | ✅ | ✅ | ✅ |
| 10 | 资产登记/导入/合并（assetlib 写） | ❌ | ❌ | ✅ | ✅ |
| 11 | 凭据入库（vault 写; 值永不回显——现律） | ❌ | ❌ | ✅ | ✅ |
| 12 | 报告签发签名（双签两把互异; 签发门 verify-signoff 同源扩展） | ❌ | ✅ | ✅ | ✅ |
| 13 | 导出（findings JSON/SARIF/账本验真包） | ❌ | ✅ | ✅ | ✅ |
| 14 | 用户管理（新建/停用/重置密码/角色分配） | ❌ | ❌ | ❌ | ✅ |
| 15 | 平台参数与设置（预算帽/保留口/告警通道） | ❌ | ❌ | ❌ | ✅ |

执法形态: webui 路由声明所属 SURFACE, `_session_ok()` 扩为 `_authz(surface)`（会话+角色双查）; 未登录=401/302（现律）, 已登录越权=403 JSON（页面同形）; SURFACE 表=代码单源+测试矩阵钉死（§六 R1 验收①）。CLI=可信面（§四 4.4 边界诚实）。

### 1.6 首启迁移（单操作员→多用户, 零断档）

升级首启检测: users.tsv 缺席且 OPERATOR_KEY 在场 → 引导建首管理员（用户名自定, 口令=OPERATOR_KEY 初值, argon2id/scrypt 落格）, 事件 admin-bootstrapped 入平台审计链; OPERATOR_KEY 此后退役（环境钥只做一次性种子）。单操作员时期账本的 actor=「人工」行**原样可读**（§五 5.1 兼容层）, 不回填不改史。

---

## 二 【必答 B】maker-checker 双签多用户化

### 2.1 现状与先例

审批=单人决定（approvals.tsv 单行 decision）; **报告签发已有双签先例**: 签发位=approvals approved 行按时间序前两卡, 「两把互异 approver=双签就绪」（api_v2_reports.py:28-29,530; task-lifecycle SIGNED=双签）。本节把「互异双签」从报告签发推广为高危决策通用门——**推广先例, 不是新范式**。

### 2.2 双签类表（DUAL_SIGN_CLASSES——低危单签维持, 高危双签, 不过度官僚）

| 类 | 触发物 | 第一签 | 第二签（互异人） |
|---|---|---|---|
| 清理核销豁免 | revert 未核销走 exempted | 操作员/审计员/管理员 | 审计员或管理员 |
| 范围修订 | amend-scope（范围外发现接入同宪法#45 分域异步门） | 任意有权签 | 非提案人 |
| 资产合并冲突 | assetlib conflict 事件（§三 3.5） | 操作员/审计员/管理员 | 审计员或管理员 |
| 报告签发 | P5.5 签发门（已实施, 纳入类表统一执法） | 操作员/审计员/管理员 | 互异人（≥1 审计员/管理员, 沿现口径） |
| 凭据授权授予 | account-grant 行 | 操作员/管理员 | 互异人 |
| 高危工具卡 | L3 档工具执行豁免 | 操作员/管理员 | 审计员或管理员 |

普通 approved/rejected（低危清理核销等）维持单签——**双签只上高危面**, 阈值进类表不进裁量。

### 2.3 执法（账本级机械拒, 不是 UI 客气）

- approve 写入时查同 command_hash 已有 approved 行: **approver 相同=REJECT duplicate-signature（同人双签机械拒）**——执法在账本写路径, 与 intents 租约双抢互斥 REJECT 同纪律。
- 双签类未满两把互异签名=状态仍 pending（**fail-closed 等人工, 不超时放行**——超时默认拒在册律不变, 这里是不设超时的挂起等待第二人）。
- maker/checker 分离: 范围修订等「提案→放行」两段动作, 提案人不得自签放行（提案行记提案人, 放行签名查互异）。
- CLI: `tanyin-ledger approve --command-hash=… --approver=<用户名> [--note=…]`（第二签自然落第二行; --counter-sign 旗标=显式声明双签档, 缺省按类表自动判）; Web: 审批卡双签位两卡+「等待复核」态+「你是第一签人, 需另一人复核」提示。
- AI 预审关系不变: judge_client 接线（W2 已排）只作 ASK 前置参考且恒标仅供参考, 终审=人（在册律）。

---

## 三 【必答 C】资产库 = 安装级真值域（跨任务登记/授权复判复用/导入合并/覆盖历史）

### 3.1 形态: 事件源真值 + 投影（不进 13 战表, 不建第二张图）

`$TANYIN_HOME/assetlib/`:

- **events.tsv**（真相层）: append-only 事件源, 行哈希链（复用 timeline.py chained_row 纪律）。列（11）: `ts, actor, kind, asset_key, type, value, meta, provenance, prev_hash, hash, schema_version`。kind 枚举: asset-upsert / asset-retire / merge / import / scope-verdict / conflict。
- **SQLite 投影**（加速层, O7 同律: **坏了删了从 events 确定性重建**）: 资产当前态表+覆盖历史表, 骑 W7 O7 落地件（~700 行在册, 先行依赖）。
- asset_key=`(type, norm(value))` 程序算（norm.py 单源）——去重键确定性与 findings dedup_key 同律。

判词: 资产库=**安装级 registry 不进 13 战表**（source-audit-v1 §三 customers/projects.tsv 同律）; 战表是执法面不是知识面, 跨战资产进战表会炸单仗哈希链的单写者域。**不建第二张图**（06-whitebox F1: 无图外状态）——资产库与任务账本靠 provenance 锚接（§3.4）。

### 3.2 跨任务登记（任务发现 → 库）

任务内发现的资产, 登记=任务结算时批量（battle settle 挂钩）或手动 `tanyin-asset register`; 登记走 CLI 单源（assetlib 模块独立 flock）——**任务不直写资产库, 单仗单写者不破**。登记事件带 provenance=battle:<N>/<资产行 id>, 血缘可回放。

### 3.3 授权复判复用（库 → 任务, 机械判定+留痕）

任务引用资产=**复判后快照导入**。复判=纯机械判定, 两道同源闸:

1. **范围闸**: scope matcher 同源（include/exclude/oob+amendment 后行覆盖; W2 扩的 url-exact/domain-fuzzy/ip-fuzzy/cidr 四 kind 自动受益——A 舰 B26 同一件）→ 三态: in（入列）/ oob（记不测, 仅 Tier3 回连）/ exclude（拒）。
2. **授权窗口闸**: goals.tsv 的 valid_from/valid_until/auth_sha256（W1 授权真化在册）→ 窗口外资产自动降 oob 并标因。

复判结论=assetlib scope-verdict 事件（每任务每资产一行: 任务/资产/判定/依据 matcher 行/窗口戳）——**复判可回放可审计**。复用=同一资产跨任务保留全血缘: 资产详情页「历史任务×判定×发现」透视（读投影）。覆盖分母不因资产库膨胀: **分母=任务 scope（denominator-ready 上锁在册）**, ARTEX planner 自扩分母的授权蔓延（活访:92 实锤）我们结构性没有。

### 3.4 快照导入（链头锚定——06-whitebox:50 裁决的落地形态）

建任务/扩范围时, 复判通过集落任务 assets.tsv: 行 provenance=`assetlib:<event-hash>`; 同时任务 timeline 落一行 `asset-snapshot-imported digest=sha256(快照) count=N`（链头锚定先例已有）。任务内对快照行的一切后续=任务账本自治（单写者域内）; 库不改不回写（要回写走 §3.2 登记门）。

### 3.5 导入合并（外部批量+冲突转审批）

- 入口: CSV/JSON 批量导入（对齐 CSAI XLSX/CSV 批量导入; B 舰 G7 同律: 解析→归一→upsert 循环→**导入回执入任务 timeline**）+外部同步适配器（ScopeSentry 等, W7 可选在册——通道进 import 门, 外部数据不过快门直接进任务）。
- 合并语义: 同 asset_key **后行胜**（amendment 同律）, 全史保留在 events——**覆盖历史=事件源永不丢**（改值=upsert 事件链, 任意历史时刻可重建）。
- 冲突: 同键跨来源 type/meta 互斥分歧=conflict 事件→**转审批队列走 §二双签裁决**（裁决人定胜负, 落 merge 事件带裁决人）; 不静默覆盖。
- 导入纪律: 值域 norm 归一+非法行拒收报告（坏行清单回执, ARTEX 向导「坏行划线禁下一步」同思想）。

### 3.6 覆盖历史（投影零新战表）

- 资产×意图族×时间（7/30/90 天窗）透视: 从各任务 timeline/matrix 投影计算（只读）——对齐 ARTEX 资产页 7/30/90 态势双折线（B 舰 B1 同件）。
- 「从未测试/超期未测」等价=matrix-gaps 消格清单（已有判定面）+资产维透视（last-tested 时间戳来自各战 gate 事件）。
- 覆盖率口径=(已覆盖+不适用)/总格 在册律不动, 资产库只加资产维切片不加新分母。

### 3.7 ARTEX 资产库逐件对照

| ARTEX 件 | 我们对等 | 判 |
|---|---|---|
| 六类资产卡+DSL 搜索（手册:297-298） | assets/edges 账本+assetlib 投影; DSL=谓词复用 query_cmds（W6 在册）+本稿 W7-A1 资产页 | 已排（W6+A1） |
| 批量导入导出+合并（CSAI 手册:99-103 同件） | §3.5 导入合并+conflict 转审批 | **已超（冲突转双签+全史事件源）** |
| 任务间共享（测试资产页签, 手册:261-262） | §3.2/3.3 登记+复判复用 | **已超（共享过授权闸, 它共享无复判）** |
| 资产覆盖图+已测高亮 | graph 页泳道+覆盖历史投影 | 已排（W6 图谱演进） |
| ScopeSentry 同步（手册:300-301） | import 门+适配器 | 已排（W7 可选, 在册） |
| 双图架构+裸两列 anchor 桥（D6） | 安装级真值域+任务过程域+provenance 锚（事件哈希级, 非裸两列） | **已超（防篡改+锚带 provenance）** |
| 力导向图（G6） | 泳道 SVG 保留 | 声明取舍（审计形态优先） |

---

## 四 【必答 D】并发模型 = 单仗单写者不变, 人=读+审批+建任务

### 4.1 不变量（三条, 施工时用测试钉死不得漂移）

1. **单仗单写者**: 每仗账本唯一语义写者=该仗 runner（战内容）; battle_registry 继续 flock 仲裁 admit/release/预算帽/端口/死 pid（§〇⑤ 全继承）。
2. **人面写=窄门**: 审批/终审/生命周期/指令/快照导入全走 CLI 子进程, flock 字节级串行（webui 零账本直写在册律）——多用户不新增第二条写路径。
3. **账本哈希链**: 一切任务账本写仍过 chained_row 单源; 资产库/用户库各自独立链（不同锁域, 互不阻塞也互不污染）。

### 4.2 N 个人的并发画像

| 动作 | 并发语义 | 复用在册件 |
|---|---|---|
| 读（页/API/SSE） | 纯只读投影, 无共享可变态; SSE 每人一连接 | W1 读面门+SSE |
| 审批 | 双抢互斥: 第二人见已决态幂等 REJECT; 双签第二签落第二行 | intents 租约 REJECT 同律 |
| 建任务 | battle_registry flock admit 仲裁（预算帽数学披露/端口互斥/保留口） | battle_registry 全件 |
| 指令/控制 | directive 文件通道+flock 串行 | say/pause 现律 |
| 资产库写 | assetlib 独立 flock 单写路径 | 账本同工艺 |
| 用户库写 | users 独立 flock+原子替换 | 同上 |

### 4.3 端口纪律

本稿新增面（用户/资产库/审计链）**全部不绑网络口**; 测试亦禁绑保留口 8900/3000/8787/8443（battle_registry FORBID_PORTS 同表, 施工验收钉⑤）。

### 4.4 边界诚实（写进设计, 不留给施工猜）

- RBAC 保护面=web/API 服务面; **OS shell 直跑 CLI=可信面**（拿到 shell 即拿到文件系统, 与 ZhuLong/CSAI 同边界）——CLI 保留 --actor/--approver 如实记名, 不做 CLI 鉴权。
- 远程节点令牌绑授权书=W7 G9 在册件, 不在本稿范围。
- 多机共享（NFS 同挂 $TANYIN_HOME）不承诺——flock 跨机语义 unknown 在册结论继承, 团队=同机多用户（一台作业机的多人门禁）, 跨机=远程节点件的事。

---

## 五 【必答 E】审计入账 = timeline actor 扩展 + 平台级审计链

### 5.1 actor 词表冻结（7 列 schema 零改, 词面扩段）

`{warrior, runner, guard, planner, knowledge, CLI, 总控, 人工(legacy), human:<用户名>}`——单值列不动, 新写人面统一 `human:alice` 形。读端兼容: 裸「人工」=单操作员时期操作员（展示为「操作员（单人时期）」）。写端: **webui 一切账本调用 --actor=human:<用户名> 由会话服务端盖戳**（客户端提交的 actor 字段忽略——防冒名是执法不是客气）; CLI 保留 --actor（可信面如实记）。

### 5.2 approvals.tsv approver 列改记用户名

现「操作员(观察面)」字面量退役, 改 `<用户名>`（如 alice）; 双签=同 command_hash 两行互异 approver; 报告签发位 verify-signoff 读法不变（互异两卡=就绪）, 数据自然多用户化。HMAC 完整性签名保留（command_hash 绑定防「批 A 行兑 B 行」）——钥归宿待裁③。

### 5.3 平台级审计链（安装级, 管理面全写面入链）

`$TANYIN_HOME/platform/audit.tsv`: 行哈希链（chained_row 同纪律, 只增律）。入链事件: 登录成功/失败/锁定、登出、会话失效、建号/改角色/停用/软删/重置密码、首启迁移、资产库全事件镜像摘要、参数变更。呈递: 用户页健康卡含**链校验通过率**（C 舰 G4: 我们的完整性计数=链校验, 比 ZhuLong WAL pragma 更硬的自观）。

### 5.4 呈递面（人话, 宪法#41）

任务详情活动流按人着色+按人筛选; 审批卡显示两签人姓名与时间; 用户页=操作留痕表（谁在何时改了谁的什么）。

---

## 六 【必答 F】W7 分阶段（量纲律#42: 只报行数+测试数, 不报时间）

> 归属: 蓝图 W7「三角色RBAC+双人复核」（07P1）施工细化, 三段合计 ~1900 行（W7 总盘 ~4500 行内子块）。依赖序: R1→R2 强依赖; A1 依赖 R1（actor/审批面）可并行 R2; A1 投影依赖 O7 落地（W7 内先行）。每段=自动收口档（纯工程批, DEV-RHYTHM-v2）+验收手册条目。

| 段 | 名 | 交付件 | 行数 | 验收钉（红→绿测试） |
|---|---|---|---|---|
| W7-R1 | **角色门** | users/sessions 存储+argon2id/scrypt 双格式+登录改版（用户名+口令）+rbac.py SURFACE 15 面+全路由挂面+actor=human: 盖戳+双签执法（duplicate-signature REJECT+类表）+首启迁移+平台审计链 | ~600 | ①越权剧本矩阵: 低权账号逐写面探（ZhuLong 伤疤剧本现成, C 舰:84）全 401/403 ②同人双签 REJECT ③裸「人工」行读兼容 ④双格式验证+登录升档+锁定 5/60s ⑤Ran N tests OK 全绿+邻面零回归 |
| W7-R2 | **用户面** | 用户管理页（导航名「用户」）+CLI user-add/list/disable/reset-password 族+自保护三律（自降级 400/自停用 403/末管理员保护）+健康卡（链校验通过率）+界面文案过 ui-copy-standard-v1 | ~500 | ①自保护三律红测 ②非 admin 探管理面全 403 ③文案规范测试（#41: 导航名词/按钮动宾/无内部代号）④Ran N tests OK |
| W7-A1 | **资产库** | assetlib events+SQLite 投影（骑 O7）+跨任务登记+授权复判（scope matcher+授权窗口同源）+快照导入链头锚定+CSV 导入合并+conflict 转双签+覆盖历史投影（7/30/90）+资产页/导入页+CLI asset-* 族 | ~800 | ①events 重放重建=投影逐字节相等（O7 同律钉）②界外资产复判拒+oob 标注留痕 ③快照 digest 验真（链头锚定行可核对）④合并冲突转审批+全史可回放（任意时刻重建）⑤测试零绑保留口 ⑥Ran N tests OK |

界面文案钉（宪法#41, 全段通用）: 导航=名词（「用户」「资产」）; 按钮=动词+宾语（「新建用户」「重置密码」「停用账户」「导入资产」「重新判定授权」）; 角色上屏=观察员/审计员/操作员/管理员; 资产授权状态上屏=「范围内/范围外/已排除」（内部词 oob/exclude/复判不上屏）; 「任务」不叫「战」（ui-copy-standard 全表继承）。

---

## 七 待裁位（随裁定案 #17 呈, 各带推荐——宪法#48）

| # | 待裁 | 选项 | 推荐+一句理由 |
|---|---|---|---|
| ① | 角色集 | a. 四档（本稿: +观察员） b. 三档（ZhuLong 形: 操作员/审计员+管理员, 无观察员） | **a 四档**——「很多人登录」含观摩/管理层只看不下场; 观察员=纯读白名单零成本档, 不加执法复杂度 |
| ② | argon2 依赖 | a. argon2id 主格式+scrypt 兜底（可选依赖, 本稿） b. 纯 stdlib scrypt（ZhuLong 同形） c. argon2-cffi 硬依赖 | **a**——argon2id 是当前口令哈希首选, 兜底保 clone 即用零依赖律不破; c 破零依赖, b 放弃现代内存硬算法 |
| ③ | TANYIN_APPROVAL_KEY 归宿 | a. 保留 HMAC 完整性签名+approver 改记用户名+环境钥退役为安装级密钥文件（本稿） b. 直接退役（会话+双签已足） | **a**——HMAC 绑 command_hash 防「批 A 行兑 B 行」的完整性价值与身份认证正交, 保留零成本; 钥从环境变量挪进 users 目录 0700 |
| ④ | 资产库真值域位置 | a. $TANYIN_HOME/assetlib 安装级（本稿） b. 13 战表加第 14 表 | **a**——战表=单仗执法面, 跨战资产进战表破单写者域+炸哈希链; source-audit-v1 customers/projects 同律先例 |

---

## 八 一句话总判

**四角色本地账户把「很多人登录开展渗透」变成执法事实（15 面读写矩阵+双签同人机械拒+actor 全链留名）; 安装级资产真值域把「ARTEX 资产库」变成更硬的形态（事件源全史+授权复判+分母不膨胀）; 单仗单写者/哈希链/CLI 单源三条铁律零改动——人是读者/审批者/建任务者, 不是第二个写者。**
