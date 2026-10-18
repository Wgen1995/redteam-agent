# authn ｜ 认证缺陷（CWE-287 认证错误 · CWE-384 会话固定）

> band: 0 ｜ 模式表: `patterns/authn-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/authn/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 密码重置毒化（Host/BaseURL 可控→重置链接发攻击者）→ High；session 固定（登录后不轮换标识）+ 固定向量可控 → High；令牌弱随机可预测（resetToken/rememberMe/sessionId）→ High；MFA 降级（二步凭据可跳过）→ High；验证码无限次/可重放 → Medium-High；JWT 签发态缺陷（alg 未钉/无 exp）→ Medium-High；框架默认 session 管理未复核 → FP 卡（需配置证据）

## ① 定义与危害
"你是谁"的判定材料可被伪造、预测或移植：口令比对错位、重置链路可劫持、会话凭据可预知或不轮换、二步凭据可绕过、令牌签发与校验不对称。危害=账号接管（重置毒化/弱令牌爆破）、会话劫持（固定+不轮换）、横向凭据复用（remember-me 伪造）。
**分型（判定与定级都按此走）**：
- **凭据生成**（CWE-330 主因挂 CWE-287）：令牌熵源弱（Random/时间戳/用户 id 派生）——锚生成行。
- **凭据校验**（CWE-287 主型）：验证码比对可绕/可重放、MFA 可降级、JWT verify 未钉 alg——锚校验行。
- **凭据生命周期**（CWE-613/CWE-384）：登录后不轮换 session 标识、令牌无有效期/用后不焚——锚轮换与过期事实。
- **凭据传输**（毒化）：重置链接的 Base URL 取自请求可控头（Host/X-Forwarded-Host）——锚 Host 取值行。
**本类为"检查缺失型"：sink 弱、判定主体在 guard 侧**。§③ 的令牌/口令/校验形态命中只证明"认证动作在此发生"；危险=**熵源、轮换、有效期、独立生效四类防护事实缺席**，由 ⑥ 差分判别。**证据面分两轨**：guards-authn 段（五段之一）只转录"入口是否要求已认证主体/显式匿名放行"（CWE-306 面向，喂 C1/C7 与入口差分），**不转录认证实现细节**（熵源/轮换/有效期/毒化由 §③ pattern 锚的生成行/校验行/轮换配置行经五步 OBS 取证）。
**认证差分**（差分轨主力信号）：按 `source_inventory.family` 的 auth 类端点族（login/logout/reset/verify/refresh 形）对照 guards-authn 转录的轮换/限次/有效期事实。**面状缺失**（全部登录路径不轮换 session=系统性默认缺失）与**点状缺失**（仅移动端 API 路径不轮换）是两种不同 finding；**同 family 令牌处置不一致→离群必解释**（同一系统里 web 路径 cycle_key 而 API 路径不轮换，离群点即 +suspicion）。

## ② Source
- **凭据材料**：口令、重置邮箱、验证码、OTP、remember-me 令牌、session 标识、JWT。
- **guard 判据输入**（C-g 专用 source）：客户端回传的"已验证"标志（`verified=true` body 字段）、localStorage 持有的 token 再提交、`X-Authenticated-User` 类信任头、URL 携带的 sessionid（固定向量）、Host/X-Forwarded-Host 头（毒化向量）。
- **存储回读（persisted_read）**：重置令牌哈希回读比对、历史 token 重放（二阶：上周作废令牌本周仍被接受）。
- guard 事实的机械来源：`langpacks/{lang}/guards-authn.md` 转录（五段之一——入口认证要求/匿名放行事实）；认证实现细节（熵源/轮换/有效期/Host 取值）按 pattern-ownership 归 §③ 锚的差分取证，不在 guards 段转录面内。

## ③ Sink 模式表指针
`patterns/authn-java.pattern` / `authn-ts.pattern` / `authn-python.pattern`（机器直读，逐行一条，不并串）。锚认证动作形态：重置族（resetPassword/passwordReset/reset_token）、口令写入（setPassword）、验证码（verify_code）、JWT 签发与校验（sign/encode/verify/decode）、session 固定形态（sessionFixation/jsessionid/sessionid）、remember-me、弱熵源（Random/Math.random/random.）、毒化注入链（Host 取值）、有效期证据（setExpiration/expiresIn/expires_delta）。**命中≠漏洞**：这些是差分轨的证据锚——生成行喂 C2 熵源判据，有效期行喂 C3，Host 取值行喂 C4；安全/危险由 ⑥ 判别。

## ④ Propagator
- **毒化传播链**：`Host`/`X-Forwarded-Host` 头 → BaseURL 拼装 → 重置链接进邮件（注入点离邮件构造可能隔多层——追到链接模板行）。
- **固定传播链**：URL 参数 sessionid → 会话查找 → 登录后沿用（`request.getSession(param)`/`sessionid` cookie 透传）。
- **信任标志传播链**：客户端校验后的 `verified` 字段进 DTO → 服务端直接信任（跨字段保守传播）。
- 令牌派生链：`userId+时间戳` 拼装、HMAC 弱密钥派生（remember-me 序列）。

## ⑤ Guard（本类的"Sanitizer"——决策表三值）
```
加密随机熵源(SecureRandom/secrets/crypto.randomBytes/uuid4) × 令牌生成 × 一次性+短时效 → 强
登录成功即轮换标识(changeSessionId/cycle_key/session.regenerate) × 全部登录路径 × 认证后 → 强
JWT 验签钉 alg 白名单+验 exp/aud/iss               × 校验点     × 每次受保护访问 → 强
限次+退避(锁定/验证码次数上限)                      × 校验失败路径 × 独立计数       → 强
时间戳/Random/用户id 派生令牌                       × 令牌生成    × 任意            → 弱(可预测)
校验码响应回显/用后不焚                             × 校验点     × 任意            → 弱(重放)
客户端回传的 verified 标志                          × 判定依据    × 任意            → 弱(等价无防护,C-g)
Host/X-Forwarded-Host 直拼 BaseURL                  × 链接构造    × 任意            → 弱(毒化向量)
框架默认 session 管理(未显式复核)                   × 任意        × 任意            → 上下文条件(挂 requires_config;FP-1)
```
**多段 guard 看全部**：口令对+OTP 对≠重放免疫（一次性缺席）；`上下文条件` 档不产生 kills 事实（框架默认未复核不得直接判弱——FP-1）。

## ⑥ 判定流程（编号条目，含第五要素 C-g）
C1 认证判定材料是否服务端生成且不可由请求指定？｜期望引用:凭据生成行与取值来源(session vs param/body/URL)｜推翻反例:材料服务端生成且单向存储(哈希/加盐)｜反向:sessionid/verified/token 可由请求参数或 URL 指定
C2 令牌熵源是什么（SecureRandom/secrets/uuid4 vs Random/Math.random/时间戳/userId 派生）？｜期望引用:生成行±3行的熵源调用与拼接材料清单｜推翻反例:加密随机+足够长度(≥128bit)｜反向:new Random(/Math.random/毫秒时间戳/短数字码且无限次
C3 令牌有效期与一次性证据（过期判定/用后即焚/重放窗口）？｜期望引用:setExpiration/expiresIn/expires_delta 行与消费后的撤销/标记已用行｜推翻反例:短时效+用后焚+撤销清单齐｜反向:无过期字段、消费后不撤销、历史 token 仍可用
C4 密码重置链路的 Base URL/Host 来源是什么（毒化向量）？｜期望引用:链接构造行±5行的 BaseURL 来源(getHeader("Host")/get_host()/X-Forwarded-Host vs 配置常量)｜推翻反例:BaseURL 为服务端配置常量且邮件域固定｜反向:Host 头或 Forwarded 头直拼进重置链接
C5 登录成功后 session 标识是否轮换（固定向量）？｜期望引用:登录成功分支的轮换调用/框架配置行(五步 OBS;§③ 的 sessionid/jsessionid 锚)｜推翻反例:认证后即轮换(changeSessionId/cycle_key/regenerate)或框架默认+配置证据｜反向:沿用认证前标识/接受 URL 或参数携带的 sessionid
C6 二步凭据（验证码/MFA）是否独立生效且限次？｜期望引用:verifyCode 校验行与其计数/退避/一次性逻辑｜推翻反例:服务端独立校验+次数上限+用后即焚｜反向:可跳过分支(remember 设备信任降级/参数关 mfa)、响应回显 code、无限次
C-g guard 输入可信性：认证判据是否取自请求可控值（客户端校验后回传的 verified/token 存前端由请求提交/信任头）？｜期望引用:判定字段的取值来源行(服务端会话存储 vs request body/header/URL)｜推翻反例:判据取服务端会话或验签 claim｜反向:verified=true 由 body 提供、token 由 localStorage 回传、X-Authenticated-User 头定身份
C7 校验失败路径是否限次（暴力面：锁定/退避/独立计数）？｜期望引用:失败分支的计数与锁定逻辑行｜推翻反例:限次+锁定+退避齐(锁定键含账号与 IP 维度)｜反向:无限次比对+响应差异可枚举用户(B8)

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 框架默认 session 管理（Django/Express/Flask 的 session id 熵与轮换由框架负责）——**需配置在场证据**（框架版本+session 配置行+无覆盖项），不得凭"用了框架"判弱，也不得凭"未显式设置"判强；复核挂 requires_config 事实。
FP-2 `jwt.verify` 在场≠安全（alg 未钉/弱密钥是 B6 变体，反向同理：verify 在场不是 FP 也不是确证——判 C2/C3 的签发侧证据）。
FP-3 测试/种子数据的固定验证码（`code=123456` 在 test fixture 作用域）——需作用域证据（测试 Profile/目录隔离），生产配置同形则立案。
FP-4 内部服务间调用的信任头（服务网格内 mTLS 已认证）——需 mTLS/网关证据，无证据不得放行（同 authz FP-2 形态）。
FP-5 登出后 token 未清但网关已拒（网关统一吊销）——需网关吊销配置 OBS。
FP-6 生成代码（role=generated 的脚手架登录页）——按生成物规约归并，不与手写同型双计。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 密码重置毒化：Host/X-Forwarded-Host 进重置链接（`https://{host}/reset?token=` 发往攻击者域；出处：PortSwigger 密码重置毒化 / Django 2013-02 Host header 安全公告同型）——链接构造行回溯 BaseURL 来源。
B2 session 固定：登录后不轮换（无 changeSessionId/cycle_key/regenerate）；sessionid 从 URL/子域 cookie 移植到登录后会话。
B3 验证码绕过：响应回显 code、4-6 位数字码无限次、校验后 `verified=true` 客户端回传复用、时间窗内重放同一 code。
B4 remember-me 弱令牌：用户名+过期串+弱密钥 HMAC（可离线爆破/伪造——Spring remember-me 默认 key 形态）；序列号自增可预测。
B5 MFA 降级：`?mfa=false`/记住设备信任降级、OTP 端点在口令校验前可直达、OIDC prompt=none 绕交互。
B6 JWT 签发/校验不对称：签发不钉 alg（none/弱 HS256 跨算法混淆）、verify 未白名单 algorithms、claim 未验 aud/iss/exp、密钥复用测试弱密钥。
B7 弱熵令牌：`new Random()`/`Math.random`/微秒时间戳 token；`random.choice` 拼 8 位"随机串"实际空间极小；6 位数字码无次数上限。
B8 用户枚举→爆破：登录/重置端点响应差异（"用户不存在"）+无限次；重置端点无限次发信（发信轰炸）。
B9 会话不过期：`setExpiration`/expiresIn 缺席或超长（30d access token）；刷新链无限续期。

## ⑨ 利用前提与定级阶梯
见页首。High 验收：账号接管链完整 OBS（毒化：Host 取值→链接构造→邮件发送；弱令牌：熵源行+爆破空间计算；固定：固定向量入口+登录沿用证据）。Medium-High 验收：绕过路径可复现（验证码重放/MFA 降级分支 OBS）。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 令牌仅内部签发、无外部可触发的重置/登录入口（OBS 无入口注册行）→ 降 medium 以下；验证码限次+一次性有引文 → low

## ⑩ 根因修复
令牌一律加密随机+短时效+一次性（用后焚+撤销清单）；登录成功即轮换 session 标识（全路径含 API）；重置链接 BaseURL 用服务端配置常量（禁 Host 头）；验证码服务端生成+限次+不回显+独立于口令判定生效；JWT 钉 alg 白名单+验 exp/aud/iss；失败路径限次锁定（账号+IP 双维度）；信任头只接受网关注入并验签。

## ⑪ 跨边界提示
Egress：服务间透传 `X-Authenticated-User` 类信任头使下游认证判据可被上游伪造（C-g 跨服务对照）；网关签发的 JWT 在下游未复验 exp（每跳独立校验）。Ingress：消息体携带的凭据材料（批量导入用户/初始化口令）走弱熵生成路径（B7 消息侧变体）；第三方回调的 OAuth code 换取链与 open-redirect B5 共用跳板证据。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 13/22/6、python 12/10/4、ts 10/10/4
`fixtures/enum/authn/{lang}/manifest.tsv`。java 全量集 pos≥10/neg≥20/noise≥5；ts、python 起步集 pos≥6/neg≥8/noise≥3。**本类特殊约定：SecureRandom/限次/轮换在场的重置与校验形态归 noise 不归 neg**——§③ 形态仍在（pattern 必然命中），安全性由 ⑥ 判别；neg 只放与认证形态易混淆的非认证形态（授权检查/哈希存储/邮件发送等）。
