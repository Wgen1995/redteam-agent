# secrets-crypto ｜ 硬编码凭据与弱密码学（CWE-798 · CWE-327）

> band: 1 ｜ 模式表: `patterns/secrets-crypto-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/secrets-crypto/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: **泄露可达即 High**（凭据在仓库/构建产物/前端 bundle/日志任一通道可达 = 已泄露面）；弱算法用于密码/会话/令牌语境 → High；弱随机仅用于非安全用途（洗牌/展示序号）→ 降 Low/清零（前提引文）
> **测试路径例外保留发卡（定稿 §3）**：本类在 `src/test`、`__tests__`、`test_*` 等测试路径**不豁免**——测试代码里的真实 key 一样会被推到仓库/CI 日志，发卡照常。

## ① 定义与危害
密钥材料（口令/API key/私钥/连接串）以字面量形式固化进源码或配置，或密码学原语选用了已破/不满足语境的算法（DES/MD5/SHA-1 用于密码、ECB 模式、`Random`/`Math.random` 生成安全值）。危害=凭据一旦进版本库即视为已泄露（历史提交不可撤回）、横向移动直达云账号/数据库/内部服务；弱算法使离线破解/频率分析/预测成为可能。依据：CWE-798/CWE-327；gitleaks/TruffleHog 规则族（aws-access-token 等）；CWE-1247（内存中暴露）为相邻类不在本表。

## ② Source
**本类无输入流——字面量即证据**。Source 语义=泄露通道枚举：源码/配置文件本身（仓库可见）、构建产物（fat-jar/前端 bundle 里内嵌 env）、错误堆栈与日志（连接串带口令打印进 log——联动 log-injection 卡）、容器镜像层、公开的 client 侧代码（TS 前端 bundle 里的 apiKey 即"永远可达"）。**`System.getenv`/`process.env`/KMS/Secrets Manager 取值不是本类**（那是凭据管理的正确形态，见 noise 目录）。

## ③ Sink 模式表指针
`patterns/secrets-crypto-java.pattern` / `secrets-crypto-ts.pattern` / `secrets-crypto-python.pattern`（机器直读，逐行一条，不并串）。形态=「字面量凭据 token」（AKIA[A-Z0-9]{16}、`-----BEGIN … PRIVATE KEY-----`、`password/apiKey/secret = "字面"`、`jdbc:…password=`、`mongodb://…@`）+「弱原语调用」（MD5/SHA-1/DES/ECB/`new Random(`/`Math.random(`/`random.choice(`）。字面量 token 是**形态即罪**；弱原语是**家族标记**，危险与否看语境（C4）。

## ④ Propagator
本类传播的是"泄露可达性"而非污点：字面量赋给常量后多处引用（`PASSWORD` 常量被三处连接复用——一处泄露即全部失守）、凭据拼进连接串/URL 后传给日志或异常消息（`logger.error(e + url)`）、前端 bundle 的 env 内联（`process.env.API_KEY` 被 webpack define 替换成字面量——构建期固化）。跨文件只追常量定义点与引用计数，不做流分析。

## ⑤ Sanitizer（决策表三值）
外部化（env/Secrets Manager/KMS/Vault 取值）→ **强**（凭据不进源码即消除形态）；`git-secrets`/gitleaks 预提交钩子 → **上下文条件（只产 hint，禁 kills——钩子可被 `--no-verify` 绕过，挂 requires_config）**；`.gitignore` 排除配置文件 → **弱**（历史提交仍在，只堵增量）；"测试用的假 key" 注释声明 → **弱**（AKIA 形态即真格式，CI 日志同样泄露）；算法侧：换 BCrypt/Argon2/PBKDF2（密码）、AES-GCM（加密）、`SecureRandom`/`crypto.randomBytes`（随机）→ **强**（对弱算法语境成立）。**多段净化看全部：env 取值后又 fallback 到硬编码字面量 = 净化失效。**

## ⑥ 判定流程（编号条目）
C1 凭据 token 是否为真形态（AKIA[A-Z0-9]{16} 全长/PEM 完整块/口令非空字面）？｜期望引用:token 所在行全量｜推翻反例:占位符（`password=""`、`password=${env}`、示例串 `xxxx`）｜反向:截断形态（AKIA 后不足 16 位）也登记但降为 hint
C2 凭据是否可达泄露通道（仓库/构建产物/bundle/日志任一）？｜期望引用:文件路径与构建配置（是否进 artifact/是否前端目录）｜推翻反例:仅本地未提交的一次性脚本且有证据｜反向:测试路径**不构成反例**（定稿 §3 例外保留发卡）
C3 弱算法调用是否在安全语境（密码存储/会话令牌/加密/MAC/盐）？｜期望引用:调用行±5 行与返回值用途（存库字段/比对/令牌签发）｜推翻反例:非安全用途（ETag/缓存键/校验和/洗牌）→ 降 Low 或清零｜反向:MD5 结果直接作口令哈希比对
C4 ECB/DES/弱随机是否存在同文件强原语替代（既有 SecureRandom 又用 Random）？｜期望引用:两种原语的 import 与调用行｜推翻反例:全文件仅强原语｜反向:强原语仅在死代码/注释里
C5 泄露面是否已扩散（历史提交/已发布镜像/已部署 bundle）？｜期望引用:git log 该文件历史、构建产物清单｜推翻反例:未提交工作区文件｜反向:token 出现在公开 npm 包/前端产物（= 已泄露，直接 High 不再问）
C6 凭据是否仍有效（可连云/可登录）？｜期望引用:无法静态判定时按"默认有效"处理并挂 blocked-on-evidence｜推翻反例:已轮换（旁证：key 前缀出现在吊销清单）｜反向:无旁证即按有效定级

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 `password = System.getenv("DB_PASSWORD")` —— 形态要求 `=` 后即引号字面，env 取值不命中；命中变体（`password = "env:DB_PWD"`）需 C1 反证引文。
FP-2 MD5 用于文件校验和/ETag/缓存键 —— 非安全语境，C3 反证清零（noise/md5-etag-checksum）。
FP-3 `new Random()` 用于测试数据/洗牌/展示序号 —— C3 反证；测试路径凭据不豁免但弱随机非安全用途照常清零。
FP-4 文档/注释里的示例 key（`AKIAIOSFODNN7EXAMPLE`）——AWS 官方文档示例串，登记为已知噪音形态；真实扫描时按 C5 单独判。
FP-5 密钥检测器自身的匹配代码（`startsWith("-----BEGIN")` 判断行）——SC-J02 命中但属检测逻辑非凭据本体（noise/pem-detection-guard）。
FP-6 `Math.random()` 于动画/延迟抖动 —— C3 反证。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 拼接/编码藏匿：`"AKIA"+"IOSFODNN7"+"EXAMPLE"`、base64/hex 编码后解码使用——形态分裂不命中，追解码行。
B2 变量间接：`String k = "…"; SecretKeySpec(k.getBytes(), "AES")`——token 在别行，靠 SecretKeySpec/IvParameterSpec 同文件共现补抓（进 §⑧ 扩清单）。
B3 连接串变体：`jdbc:…?user=x&password=y` 命中，但 `user=x;password=y`（分号分隔）同样成立——SC-J07 只认 `password=`，形态一致即命中，注意大小写 `PASSWORD=` 由 J04 兜。
B4 弱算法变体：`DigestUtils.md5Hex(` 命中，`MessageDigest.getInstance("md5")`（小写）不命中 J08——大小写变体进 B 列表复核。
B5 Git 历史：工作区已外部化但 `git log -p` 仍含旧字面量——泄露可达性以历史为准（C5）。
B6 前端 bundle：源码 `process.env.KEY` 看似外部化，webpack `DefinePlugin` 构建期替换成字面量——读构建配置再定。
B7 python `getrandbits(`/`randrange(`、java `ThreadLocalRandom`/`UUID.randomUUID` 误用语境——未列家族，进 B 清单。

## ⑨ 利用前提与定级阶梯
见页首。**泄露可达即 High**——不需要完整攻击链叙述：凭据 token 达到任一泄露通道（仓库可见=最低门槛）即满足 High 验收；专业审查者的验收问题只有"这个 key 真能用吗"，静态给不出答案时挂 blocked-on-evidence 而非降级。band:1 与 band:0 的差别：发卡前必须闭合 C1（真形态）与 C2（泄露通道）两问，占位符与环境变量取值是最常见清零路径；字面量 token（AKIA/PEM 全形态）判定链最短，弱算法调用必须逐卡走 C3 语境判定。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 测试/示例凭据（role=test 引文）或值已脱敏/占位符形态 → 降 info

## ⑩ 根因修复
凭据一律外部化（env/Secrets Manager/KMS/Vault），仓库加 gitleaks/git-secrets 预提交钩子并堵 `--no-verify`；已泄露凭据立即轮换（改代码不改轮换=无效修复）；密码存储换 Argon2id/bcrypt/PBKDF2；对称加密 AES-GCM（禁 ECB）；随机一律 SecureRandom/crypto.randomBytes/secrets；前端产物禁止内嵌任何凭据（代理转发到后端取）。

## ⑪ 跨边界提示
CI/CD 流水线把 repo 字面量注入构建环境再打进镜像（镜像层泄露=第二泄露通道）；微服务间共享的"内部 token"进公共库（一处泄露全网失守）；日志侧连接串带口令打印联动 log-injection 卡（凭据落日志=双向都发卡）；前端 bundle 泄露属"永远可达"，不受服务端边界保护。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 13/23/6、python 10/10/3、ts 9/12/4
`fixtures/enum/secrets-crypto/{lang}/manifest.tsv`（java 达标集：正例≥10/硬负例≥20/噪音≥5；ts/python 起步集——见 classes/fixture-spec.md 三类语义）。
