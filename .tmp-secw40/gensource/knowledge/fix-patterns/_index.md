# 标准修复模式知识库索引维护规范（fix-patterns/）

`index_version: 2.1.0`
`declared_count: 141`
`count_source: index_rows`

> 来源：决策文档 `docs/research/decision/16-gensource-container-design-spec.md`（#16容器设计，已确认）第4节确定的存储形态；`docs/research/decision/24-category15-knowledge-organization-spec.md`（#15知识组织与检索，已确认）第4/5节索引结构/知识条目内部结构/强制显式查阅纪律/接口约束；`docs/research/decision/31-category13-language-stack-adaptation-spec.md`（#13语言/技术栈适配，已确认）第5节"适用语言/框架"字段要求；`docs/research/decision/25-category12-scale-cost-management-spec.md`（#12规模成本管理，已确认）第4节索引规模应对方案；`docs/research/decision/06-category-scoring-and-recommendations.md`（早期跨竞品打分框架，内容层面仍有效）F1/F2结论；`docs/research/decision/22-category07-remediation-guidance-spec.md`（#7修复指导，已确认）关于窄范围战术修复与证据标签的既有结论。本文件是上述决策规格落地到`knowledge/fix-patterns/`目录后的**索引维护规范**。

**状态声明（历史声明，现已过时——保留作沿革记录）**：本目录曾长期不含任何实际知识条目。2026-08-08，基于GenSource对dvpwa（Damn Vulnerable Python Web App）测试靶场的一次真实实测审计，首批4个知识条目已落地（见第2节索引表），条目内容均有具体文件/行号证据支撑（或转译自项目已验证生效的对照写法/行业标准实践，详见各条目引用分级标注），不是编造内容。条目数量仍很少，覆盖面远未完整，未来仍需持续积累。

## 1. 这个目录解决什么问题（用途与消费方）

`fix-patterns/`收录**标准修复模式知识**：给定一个已确认漏洞对应的漏洞模式，标准、可复用的修复动作该是什么（如"未参数化SQL拼接"对应"改为参数化查询/预编译语句"）。这类知识服务的是`remediation-guidance/SKILL.md`（#7修复指导）已确立的**两种修复模式**中的**窄范围战术修复**——不服务架构性加固提案（那属于跨多个根因组的聚类判断，不是模式驱动，见`remediation-guidance/SKILL.md`步骤A/B2）。

**消费方**：`skills/remediation-guidance/SKILL.md`（#7修复指导）步骤B1"窄范围战术修复"。该文件已把`knowledge/fix-patterns/`列为必填输入（"窄范围修复时必填"），输出字段`fix_pattern_ref`直接对应"命中的`knowledge/fix-patterns/`知识库条目引用"。

**不服务的场景**：架构性加固提案（步骤B2）不查本目录，其聚类依据是"被违反的不变量/信任边界/控制归属方"，不是模式匹配；本目录不收录"什么代码信号意味着有漏洞"（那是`vuln-patterns/`）或攻击利用手法（那是`attack-patterns/`）。

## 2. 索引表格格式规范

索引是"扫一眼就知道该不该细看"的轻量表格，不是按字母顺序随便列的清单。列定义：

| 列名 | 含义 |
|---|---|
| 条目ID | 唯一标识，指向`fix-patterns/`下对应的条目文件（文件命名规则见第3节） |
| 触发信号 | 什么信号出现时该套用这条修复——典型是"命中的vuln-pattern条目ID/CWE类别"（如"命中`vuln-patterns/`某未参数化SQL拼接条目" → 该套用参数化查询修复），不是模糊的漏洞类型名称 |
| 适用语言/框架 | 本条目适用的语言/框架范围（#13已确认要求新增此列）。修复动作的具体实现天然语言相关（如参数化查询在不同语言的具体API不同），支持按#1/#2产出的语言/框架事实过滤 |
| 一句话摘要 | 一句话说明这条修复模式的动作是什么 |
| 交叉引用 | **反向关联的`vuln-patterns/`条目ID**（本修复模式对应哪些漏洞模式）。与`vuln-patterns/_index.md`里各条目记录的"对应fix-pattern条目ID"互为镜像——新增/变更任一侧的交叉引用时，必须同步核对另一侧，避免单向漂移（未在#15决策文档中逐字规定，是维持#15已确认的"三个知识子目录之间要有交叉引用"这一原则在双向一致性上的必然要求，不是新机制） |

**当前索引表（141条）**。计数以本文件唯一`FIX-*`数据行为准，覆盖目录内全部正式条目文件：

| 条目ID | 触发信号 | 适用语言/框架 | 一句话摘要 | 交叉引用（对应的vuln-pattern条目ID） |
|---|---|---|---|---|
| FIX-SQLI-PARAMQUERY-01（`sql-parameterized-query.md`） | 命中`VULN-SQLI-STRCONCAT-01` | 所有DB-API风格驱动（Python psycopg2/aiopg/sqlite3、Java PreparedStatement、Node pg/mysql2等），验证案例Python+aiopg | 把字符串拼接/格式化构造SQL改为驱动提供的参数化占位符，参数与SQL文本分离传输 | VULN-SQLI-STRCONCAT-01 |
| FIX-XSS-AUTOESCAPE-01（`enable-template-autoescape.md`） | 命中`VULN-XSS-AUTOESCAPE-01` | Jinja2/Django Templates/Twig等有全局autoescape开关的模板引擎，验证案例Jinja2(aiohttp_jinja2) | 模板引擎初始化设置autoescape=True，需保留原始HTML处逐处用`|safe`/`mark_safe`标注例外 | VULN-XSS-AUTOESCAPE-01 |
| FIX-CRYPTO-STRONGHASH-01（`salted-strong-password-hash.md`） | 命中`VULN-CRYPTO-WEAKHASH-01` | 不限语言，密码存储逻辑处均适用（Python bcrypt/pbkdf2_hmac、Java BCryptPasswordEncoder、PHP password_hash()等） | 改用bcrypt/argon2/pbkdf2/scrypt等专用密码哈希函数（内置加盐+可调工作因子），替代md5/sha1等通用哈希直接比较 | VULN-CRYPTO-WEAKHASH-01 |
| FIX-AUTHZ-ADDCHECK-01（`add-authorization-decorator.md`） | 命中`VULN-AUTHZ-MISSING-01` | 所有有装饰器/中间件式授权机制的Web框架，验证案例Python aiohttp自定义装饰器 | 为状态变更端点补齐授权检查装饰器/中间件，且须先核实该端点应属的权限级别，不可不假思索统一套用同一级别 | VULN-AUTHZ-MISSING-01 |
| FIX-XSS-OUTPUT-ENCODING-01（`raw-output-escaping.md`） **[新建，Inferred]** | 命中`VULN-XSS-RAWOUTPUT-01` | 原生PHP/原生JSP/任何不经过模板引擎的原生输出场景 | 输出前统一调用HTML转义函数（htmlspecialchars/html.escape等），或改用带自动转义的模板引擎 | VULN-XSS-RAWOUTPUT-01 |
| FIX-DEADCONTROL-ASSEMBLY-01（`dead-control-assembly.md`） **[新建，Inferred]** | 命中`VULN-HYGIENE-DEADCONTROL-01` | 不限语言/框架，任何需显式装配才生效的安全机制架构 | 装配已实现但未引用的安全控制——中间件加入注册链、校验schema接入调用点、分级参数按业务核实后接入 | VULN-HYGIENE-DEADCONTROL-01 |
| FIX-INJ-SPECELEM-01（`inj-special-element-neutralization.md`） **[Inferred]** | 命中`VULN-INJ-SPECELEM-01` | 不限语言/框架，日志/CSV/EL/模板引擎场景 | 按目标解释器上下文中和特殊元素——移除/转义特殊字符或改用安全的数据传递方式 | VULN-INJ-SPECELEM-01 |
| FIX-INJ-CMD-01（`inj-command-argument-array.md`） | 命中`VULN-INJ-CMD-01` | Python/PHP/Java/Node.js/Go/Ruby等所有执行shell命令的语言，验证案例Python | 改为参数数组形式执行命令（shell=False+列表参数），shell解释器不介入 | VULN-INJ-CMD-01 |
| FIX-INJ-RESOURCE-01（`inj-resource-identifier-whitelist.md`） | 命中`VULN-INJ-RESOURCE-01` | Python/PHP/Java/Node.js/Go等所有将外部输入用作资源标识符的语言，验证案例Python | 白名单/规范化/前缀绑定校验资源标识符，确保资源访问仅限于预期范围 | VULN-INJ-RESOURCE-01 |
| FIX-INJ-CRLF-01（`inj-crlf-stripping.md`） **[Inferred]** | 命中`VULN-INJ-CRLF-01` | Python/Java/PHP/Node.js等所有构造行结构数据的语言 | 移除/拒绝CRLF字符或升级到内置CRLF过滤的框架版本 | VULN-INJ-CRLF-01 |
| FIX-INJ-CODE-01（`inj-code-no-dynamic-eval.md`） | 命中`VULN-INJ-CODE-01` | Python/JavaScript/PHP/Java/Ruby等所有支持动态代码执行的语言，验证案例Python | 改用安全替代（JSON解析/模板变量传递）或白名单表达式校验，不使用eval/exec处理外部输入 | VULN-INJ-CODE-01 |
| FIX-INJ-FMTSTR-01（`inj-format-string-fixed-template.md`） **[Inferred]** | 命中`VULN-INJ-FMTSTR-01` | C/C++/PHP等使用格式化字符串机制的语言 | 改为固定格式字符串+可控值在数据参数位（printf("%s", user_input)而非printf(user_input)） | VULN-INJ-FMTSTR-01 |
| FIX-INJ-XXE-01（`inj-xxe-disable-entities.md`） **[Inferred]** | 命中`VULN-INJ-XXE-01` | Java/Python(lxml)/PHP/.NET等所有解析XML的语言 | 禁用XML解析器外部实体/DTD/外部参数实体处理，或使用安全替代库（如defusedxml） | VULN-INJ-XXE-01 |
| FIX-INJ-SSRF-01（`inj-ssrf-url-whitelist.md`） | 命中`VULN-INJ-SSRF-01` | Python/Java/Node.js/PHP/Go等所有支持HTTP客户端库的语言，验证案例Python | 白名单域名+协议限制+内部地址段过滤，确保服务端网络请求仅发向允许的外部资源 | VULN-INJ-SSRF-01 |
| FIX-INJ-DESERIAL-01（`inj-deserialization-type-whitelist.md`） | 命中`VULN-INJ-DESERIAL-01` | Python/Java/PHP/.NET/Ruby等所有支持原生对象序列化的语言，验证案例Python | 改用安全数据格式（JSON）或类型白名单受限反序列化（RestrictedUnpickler/ObjectInputFilter/allowed_classes） | VULN-INJ-DESERIAL-01 |
| FIX-CONC-RACE-01（`conc-race-atomic-synchronization.md`） **[Inferred]** | 命中`VULN-CONC-RACE-01` | Python/Java/C/C++/Go/Node.js等所有支持并发的语言 | 添加原子性同步保证——文件用O_NOFOLLOW+fstat，数据库用事务+FOR UPDATE，内存用锁覆盖完整临界区 | VULN-CONC-RACE-01 |
| FIX-CONC-LOCKING-01（`conc-locking-proper-release.md`） **[Inferred]** | 命中`VULN-CONC-LOCKING-01` | Python/Java/C++/Go/C等所有提供锁机制的语言 | 正确的锁获取/释放——with/try-finally/RAII保证所有路径释放+统一锁顺序避免死锁 | VULN-CONC-LOCKING-01 |
| FIX-EXC-UNCHECKED-01（`exc-unchecked-check-return-value.md`） **[Inferred]** | 命中`VULN-EXC-UNCHECKED-01` | C/C++/Go/Python/Java等所有有可失败函数调用的语言 | 检查返回值并安全处理错误——添加返回值检查，失败时返回错误/终止/安全默认值 | VULN-EXC-UNCHECKED-01 |
| FIX-EXC-SWALLOWED-01（`exc-swallowed-proper-handling.md`） **[Inferred]** | 命中`VULN-EXC-SWALLOWED-01` | Python/Java/JavaScript/C#/PHP等所有有异常处理的语言 | 正确的异常处理——catch/except块内添加日志+拒绝/终止+缩小到具体异常类型 | VULN-EXC-SWALLOWED-01 |
| FIX-EXC-FAILOPEN-01（`exc-failopen-fail-closed.md`） **[Inferred]** | 命中`VULN-EXC-FAILOPEN-01` | 不限语言/框架，任何有安全检查逻辑的代码 | 改为fail-closed——安全检查失败时返回401/403/拒绝而非默认允许 | VULN-EXC-FAILOPEN-01 |
| FIX-CALC-INTOVERFLOW-01（`calc-integer-overflow-check.md`） **[Inferred]** | 命中`VULN-CALC-INTOVERFLOW-01` | C/C++/Java/Go/Rust/Python等所有有数值计算的语言 | 添加溢出检查和安全计算——运算前溢出检查或使用__builtin_mul_overflow/checked_mul等安全API | VULN-CALC-INTOVERFLOW-01 |
| FIX-CALC-COMPARE-01（`calc-comparison-correct-equals.md`） **[Inferred]** | 命中`VULN-CALC-COMPARE-01` | Java/C/C++/JavaScript/PHP/Python等所有有比较操作的语言 | 使用正确的比较方式和常量时间比较——==改equals/strcmp判断改==0/安全比较用hmac.compare_digest | VULN-CALC-COMPARE-01 |
| FIX-CALC-INCOMPLETE-01（`calc-incomplete-full-comparison.md`） **[Inferred]** | 命中`VULN-CALC-INCOMPLETE-01` | 不限语言/框架，密码比较/令牌验证/权限检查场景 | 改为包含所有必要因子的完整比较——只比较长度的改为完整内容比较/strncmp改为strcmp | VULN-CALC-INCOMPLETE-01 |
| FIX-CALC-LENGTH-01（`calc-length-validation.md`） **[Inferred]** | 命中`VULN-CALC-LENGTH-01` | C/C++/Python(ctypes)/Go/Rust(unsafe)等所有有缓冲区操作的语言 | 添加长度参数一致性验证——缓冲区操作前验证len<=available且len<=sizeof(buf)或使用memcpy_s | VULN-CALC-LENGTH-01 |
| FIX-PROT-CLIENTSIDE-01（`prot-clientside-server-side-validation.md`） **[Inferred]** | 命中`VULN-PROT-CLIENTSIDE-01` | 不限语言/框架，Web前端+服务端 | 添加服务端验证作为客户端控制的后盾——每个客户端验证规则在服务端也独立执行 | VULN-PROT-CLIENTSIDE-01 |
| FIX-PROT-OBSCURITY-01（`prot-obscurity-independent-controls.md`） **[Inferred]** | 命中`VULN-PROT-OBSCURITY-01` | 不限语言/框架，隐藏URL/自定义算法场景 | 添加独立于隐蔽性的安全控制——隐藏面板添加认证/授权，自定义算法替换为标准密码学 | VULN-PROT-OBSCURITY-01 |
| FIX-PROT-SINGLEFACTOR-01（`prot-singlefactor-add-mfa.md`） **[Inferred]** | 命中`VULN-PROT-SINGLEFACTOR-01` | Python/Java/Node.js/Go等支持TOTP/WebAuthn的语言 | 添加多因素认证/step-up认证——认证添加MFA/2FA，特权操作要求近期完成MFA | VULN-PROT-SINGLEFACTOR-01 |
| FIX-PROT-GUESSABLE-01（`prot-guessable-strong-captcha.md`） **[Inferred]** | 命中`VULN-PROT-GUESSABLE-01` | Web应用(CAPTCHA服务)、Python/JavaScript/PHP | 使用专业CAPTCHA服务或增强挑战复杂度——reCAPTCHA v3/hCaptcha或大答案空间+随机化+噪声 | VULN-PROT-GUESSABLE-01 |
| FIX-PROT-ADMINCTRL-01（`prot-adminctrl-configurable-security.md`） **[Inferred]** | 命中`VULN-PROT-ADMINCTRL-01` | 不限语言/框架，SaaS/企业应用管理接口 | 添加管理员安全配置能力和审计日志——安全设置改为可配置+审计日志查看界面 | VULN-PROT-ADMINCTRL-01 |
| FIX-CRYPTO-ENFORCEENC-01（`enforce-encryption-tls-atrest.md`） **[Inferred]** | 命中`VULN-CRYPTO-NOENCRYPT-01` | 不限语言，传输侧(requests/HttpsURLConnection/https)与存储侧(Fernet/JCA/crypto)均适用 | 传输层强制TLS+存储层字段/卷级加密+日志脱敏，移除`verify=False`/`InsecureSkipVerify` | VULN-CRYPTO-NOENCRYPT-01 |
| FIX-CRYPTO-ADEQUATESTRENGTH-01（`use-adequate-crypto-strength.md`） **[Inferred]** | 命中`VULN-CRYPTO-WEAKSTRENGTH-01` | Python(cryptography)/Java(JCA)/Node(crypto/bcrypt)/Go(crypto/rsa)等所有加密API | 加密强度参数提升至安全基线——对称≥128位/RSA≥2048/KDF迭代达数十毫秒 | VULN-CRYPTO-WEAKSTRENGTH-01 |
| FIX-CRYPTO-CSPRNG-01（`use-csprng-for-security-values.md`） **[Inferred]** | 命中`VULN-CRYPTO-WEAKRNG-01` | Python(secrets/os.urandom)/Java(SecureRandom)/Node(crypto.randomBytes)/Go(crypto/rand) | 安全场景用CSPRNG生成随机值(令牌/密钥/IV/nonce/盐)且≥128位，移除可预测种子 | VULN-CRYPTO-WEAKRNG-01 |
| FIX-CRYPTO-VERIFYAUTH-01（`verify-data-authenticity-signature.md`） **[Inferred]** | 命中`VULN-CRYPTO-NOAUTHVERIFY-01` | Python(requests/gnupg/hashlib)/Java(JCA Signature)/Node(crypto.verify)/Go(crypto/rsa) | 验证外部数据来源真实性与完整性——签名验证+TLS证书校验启用+完整性校验 | VULN-CRYPTO-NOAUTHVERIFY-01 |
| FIX-CRYPTO-ORIGIN-01（`enforce-origin-validation-csrf.md`） **[Inferred]** | 命中`VULN-CRYPTO-NOORIGIN-01` | Django(CsrfViewMiddleware)/Flask(CSRFProtect)/Express(csurf)/Spring(CSRFFilter)及WebSocket | 强制来源验证——CSRF token与会话绑定+SameSite Cookie+CORS限制Origin+WebSocket Origin校验 | VULN-CRYPTO-NOORIGIN-01 |
| FIX-CRYPTO-KEYLIFE-01（`proper-key-lifecycle-rotation.md`） **[Inferred]** | 命中`VULN-CRYPTO-KEYLIFE-01` | Python(cryptography/os.urandom)/Java(JCA/KMS)/Node(crypto.randomBytes)/Go(crypto/rand) | 正确的密钥/nonce生命周期管理——CSPRNG唯一nonce+KMS密钥+轮换撤销+调试生产分离 | VULN-CRYPTO-KEYLIFE-01 |
| FIX-CRYPTO-AEAD-01（`complete-crypto-steps-aead.md`） **[Inferred]** | 命中`VULN-CRYPTO-MISSINGSTEP-01` | Python(cryptography AESGCM)/Java(JCA GCM)/Node(crypto gcm)/Go(chacha20poly1305) | 用AEAD补齐密码学步骤——AES-GCM/ChaCha20-Poly1305一步到位或encrypt-then-MAC+密钥协商认证 | VULN-CRYPTO-MISSINGSTEP-01 |
| FIX-MEM-BOUNDS-01（`mem-bounds-safe-functions.md`） **[Inferred]** | 命中`VULN-MEM-BOUNDS-01` | C(snprintf/strncpy+终止符)/C++(std::span)/Rust(安全切片)/Python(bytes)/Java(ByteBuffer)/Go(copy) | 使用带边界检查的安全函数或添加显式边界检查Guard | VULN-MEM-BOUNDS-01 |
| FIX-MEM-INDEX-01（`mem-index-bounds-check.md`） **[Inferred]** | 命中`VULN-MEM-INDEX-01` | C(手动if)/C++(at())/Rust(get())/Python(原生)/Java(List.get)/Go(切片) | 补齐索引范围检查或改用at()/get()等带边界检查的访问方式 | VULN-MEM-INDEX-01 |
| FIX-MEM-LAYOUT-01（`mem-layout-explicit-parse.md`） **[Inferred]** | 命中`VULN-MEM-LAYOUT-01` | C(ntohl/位移)/Rust(zerocopy)/Python(struct.unpack)/Java(ByteBuffer)/Go(encoding/binary) | 改用逐字段显式解析替代整体结构体memcpy | VULN-MEM-LAYOUT-01 |
| FIX-MEM-NULLTERM-01（`mem-nullterm-termination.md`） **[Inferred]** | 命中`VULN-MEM-NULLTERM-01` | C(snprintf/strncpy+终止符)/C++(std::string)/Rust(CString) | 使用snprintf（自动终止）或拷贝后显式设置buf[n-1]='\0' | VULN-MEM-NULLTERM-01 |
| FIX-MEM-PTR-01（`mem-ptr-no-external.md`） **[Inferred]** | 命中`VULN-MEM-PTR-01` | C(kernel copy_to_user/copy_from_user)/Rust(不使用unsafe) | 不接受外部指针，使用copy_to_user/copy_from_user安全替代或内核内分配并返回 | VULN-MEM-PTR-01 |
| FIX-FILE-TRAVERSAL-01（`file-traversal-canonicalize.md`） **[Inferred]** | 命中`VULN-FILE-TRAVERSAL-01` | C(realpath)/C++(canonical)/Rust(canonicalize)/Python(realpath)/Java(getCanonicalPath)/Go(filepath.Clean) | 路径规范化+前缀验证或白名单映射 | VULN-FILE-TRAVERSAL-01 |
| FIX-FILE-SYMLINK-01（`file-symlink-nofollow.md`） **[Inferred]** | 命中`VULN-FILE-SYMLINK-01` | C(O_NOFOLLOW)/Rust(symlink_metadata)/Python(O_NOFOLLOW)/Java(LinkOption)/Go(O_NOFOLLOW) | 使用O_NOFOLLOW标志或先解析链接目标再验证 | VULN-FILE-SYMLINK-01 |
| FIX-FILE-PATHEQUIV-01（`file-pathequiv-canonicalize.md`） **[Inferred]** | 命中`VULN-FILE-PATHEQUIV-01` | C(realpath+strcasecmp)/Rust(canonicalize)/Python(normpath+realpath+.lower)/Java(getCanonicalPath) | 路径规范化后再做安全检查 | VULN-FILE-PATHEQUIV-01 |
| FIX-FILE-VIRTUAL-01（`file-virtual-safe-filename.md`） **[Inferred]** | 命中`VULN-FILE-VIRTUAL-01` | C(UUID)/Rust(uuid)/Python(secure_filename)/Java(UUID)/Go(uuid) | 安全文件名生成+虚拟资源名过滤 | VULN-FILE-VIRTUAL-01 |
| FIX-FILE-SEARCHPATH-01（`file-searchpath-absolute.md`） **[Inferred]** | 命中`VULN-FILE-SEARCHPATH-01` | C/C++(绝对路径execv)/Rust(绝对路径)/Python(绝对路径subprocess)/Java(System.load)/Go(绝对路径) | 使用绝对路径加载+搜索路径信任验证 | VULN-FILE-SEARCHPATH-01 |
| FIX-FILE-TEMPFILE-01（`file-tempfile-mkstemp.md`） **[Inferred]** | 命中`VULN-FILE-TEMPFILE-01` | C(mkstemp)/Rust(tempfile crate)/Python(tempfile.mkstemp)/Java(Files.createTempFile)/Go(os.CreateTemp) | 使用mkstemp等安全临时文件创建方式（随机名+O_EXCL+0600） | VULN-FILE-TEMPFILE-01 |
| FIX-INPUT-VALIDATION-01（`input-validation-framework.md`） **[Inferred]** | 命中`VULN-INPUT-VALIDATION-01` | Rust(serde+validator)/Python(Pydantic)/Java(Bean Validation)/Go(go-playground/validator)/Node(Joi) | 使用验证框架或显式白名单验证输入的格式/长度/范围/类型/结构 | VULN-INPUT-VALIDATION-01 |
| FIX-INPUT-XML-01（`input-xml-disable-entities.md`） **[Inferred]** | 命中`VULN-INPUT-XML-01` | C/C++(libxml2安全选项)/Rust(限制实体)/Python(defusedxml)/Java(安全配置)/PHP(libxml_disable)/.NET(DtdProcessing) | 禁用外部实体/DTD/实体扩展或使用安全替代库（defusedxml） | VULN-INPUT-XML-01 |
| FIX-INPUT-MISPARSE-01（`input-misparse-canonical-decode.md`） **[Inferred]** | 命中`VULN-INPUT-MISPARSE-01` | 通用(一次性规范解码)/Python(unquote一次)/Java(URLDecoder一次)/Go(QueryUnescape一次) | 一次性规范解码后在规范形式上验证和使用 | VULN-INPUT-MISPARSE-01 |
| FIX-INPUT-SPECELEM-01（`input-specelem-structure-check.md`） **[Inferred]** | 命中`VULN-INPUT-SPECELEM-01` | C(strtok+计数)/Rust(split+模式匹配)/Python(split+len)/Java(split+length)/Go(Split+len) | 解析后检查结构完整性或使用类型安全解析方式 | VULN-INPUT-SPECELEM-01 |
| FIX-INPUT-CASE-01（`input-case-normalize.md`） **[Inferred]** | 命中`VULN-INPUT-CASE-01` | C(strcasecmp)/Rust(to_lowercase)/Python(.lower()/.casefold)/Java(equalsIgnoreCase)/Go(ToLower/EqualFold) | 统一大小写处理策略后再比较和操作 | VULN-INPUT-CASE-01 |
| FIX-INPUT-COLLAPSE-01（`input-collapse-normalize-first.md`） **[Inferred]** | 命中`VULN-INPUT-COLLAPSE-01` | C/C++(ICU)/Rust(unicode-normalization)/Python(unicodedata.normalize)/Java(Normalizer)/Go(x/text/norm) | 先规范化/转换再在规范形式上验证和使用 | VULN-INPUT-COLLAPSE-01 |
| FIX-INPUT-HANDLING-01（`input-handling-complete-checks.md`） **[Inferred]** | 命中`VULN-INPUT-HANDLING-01` | C(手动检查)/Rust(Result/Option)/Python(isinstance+try-except)/Java(instanceof+Optional)/Go(类型断言) | 补齐类型检查+边界值检查+缺失/多余参数处理+异常捕获 | VULN-INPUT-HANDLING-01 |
| FIX-INPUT-REGEX-01（`input-regex-fix-anchors.md`） **[Inferred]** | 命中`VULN-INPUT-REGEX-01` | C/C++(PCRE+避免嵌套)/Rust(regex线性时间)/Python(fullmatch+{1,100})/Java(matches())/Go(regexp RE2) | 修正正则锚点+长度限制+避免ReDoS或使用线性时间引擎 | VULN-INPUT-REGEX-01 |
| FIX-INPUT-INVALIDSTRUCT-01（`input-invalidstruct-strict-parse.md`） **[Inferred]** | 命中`VULN-INPUT-INVALIDSTRUCT-01` | C(错误码检查)/Rust(Result)/Python(try-except)/Java(try-catch)/Go(error检查) | 使用严格模式解析器+异常捕获+Schema验证 | VULN-INPUT-INVALIDSTRUCT-01 |
| FIX-RES-CONSUMPTION-LIMIT-01（`res-add-consumption-limits.md`） **[Inferred]** | 命中`VULN-RES-UNCONTROLLED-01` | Python Flask/Django+Java Spring+Node.js Express+Go+PHP+Nginx | 添加资源消耗限制——大小/频率/连接数上限 | VULN-RES-UNCONTROLLED-01 |
| FIX-RES-RELEASE-01（`res-guaranteed-release.md`） **[Inferred]** | 命中`VULN-RES-RELEASE-01` | Python(with)/Java(try-with-resources)/C++(RAII)/Go(defer)/PHP(try-finally) | 保证资源释放——with/try-with-resources/RAII/defer | VULN-RES-RELEASE-01 |
| FIX-RES-ITERATION-01（`res-iteration-upper-bound.md`） **[Inferred]** | 命中`VULN-RES-ITERATION-01` | Python/Java/C/C++/Go等所有语言 | 添加循环迭代上限——max_iterations/超时 | VULN-RES-ITERATION-01 |
| FIX-RES-RECURSION-01（`res-recursion-depth-limit.md`） **[Inferred]** | 命中`VULN-RES-RECURSION-01` | 不限语言/框架 | 添加递归深度限制——max_depth参数 | VULN-RES-RECURSION-01 |
| FIX-RES-COMPLEXITY-01（`res-complexity-bound.md`） **[Inferred]** | 命中`VULN-RES-COMPLEXITY-01` | Python re2/Go regexp/Rust regex/通用(输入上限+超时) | 控制算法复杂度——RE2/输入上限/超时 | VULN-RES-COMPLEXITY-01 |
| FIX-RES-FREQUENCY-01（`res-add-rate-limiting.md`） **[Inferred]** | 命中`VULN-RES-FREQUENCY-01` | Python flask-limiter/django-ratelimit+Java bucket4j+Node.js express-rate-limit+Go+PHP Laravel | 添加速率限制——频率/操作次数约束 | VULN-RES-FREQUENCY-01 |
| FIX-RES-POOL-01（`res-pool-sizing-timeout.md`） **[Inferred]** | 命中`VULN-RES-POOL-01` | Python SQLAlchemy/Java HikariCP/Node.js pg/Go database/sql | 合理池容量配置+获取超时+降级 | VULN-RES-POOL-01 |
| FIX-RES-UAF-01（`res-null-after-release.md`） **[Inferred]** | 命中`VULN-RES-UAF-01` | C++(unique_ptr/shared_ptr)/C(free+NULL)/Python(with)/Java(try-with-resources)/Rust(Box) | 释放后置空引用+使用自动管理结构 | VULN-RES-UAF-01 |
| FIX-RES-REFCOUNT-01（`res-refcount-pairing.md`） **[Inferred]** | 命中`VULN-RES-REFCOUNT-01` | C++(shared_ptr)/Rust(Rc/Arc)/C(atomic)/Obj-C(ARC) | 引用计数配对完整性+原子更新 | VULN-RES-REFCOUNT-01 |
| FIX-RES-INIT-01（`res-initialize-before-use.md`） **[Inferred]** | 命中`VULN-RES-INIT-01` | C(calloc/memset)/C++(构造函数)/Go(make)/Python(初值)/Rust(编译期) | 分配即初始化——calloc/构造函数/零值验证 | VULN-RES-INIT-01 |
| FIX-RES-MULTIOP-01（`res-operation-idempotency.md`） **[Inferred]** | 命中`VULN-RES-MULTIOP-01` | 通用(唯一约束/幂等key)/C/C++(置空)/Python(状态标志)/分布式(锁) | 操作幂等性保证——状态守卫/幂等key/分布式锁 | VULN-RES-MULTIOP-01 |
| FIX-RES-PHASE-01（`res-phase-state-guard.md`） **[Inferred]** | 命中`VULN-RES-PHASE-01` | 通用(状态机/状态守卫)/Java(状态验证异常)/Python(状态检查) | 添加生命周期阶段状态守卫 | VULN-RES-PHASE-01 |
| FIX-RES-DUPID-01（`res-unique-identifier.md`） **[Inferred]** | 命中`VULN-RES-DUPID-01` | Python(uuid4)/Java(UUID)/Node.js(crypto.randomUUID)/分布式(Snowflake)/数据库(UNIQUE) | 使用保证唯一的标识符生成机制 | VULN-RES-DUPID-01 |
| FIX-RES-EMERGENT-01（`res-emergent-resource-management.md`） **[Inferred]** | 命中`VULN-RES-EMERGENT-01` | Python(tempfile)/通用(缓存TTL/临时表/定时清理) | 涌现资源纳入生命周期管理——注册/清理/访问控制 | VULN-RES-EMERGENT-01 |
| FIX-CFLOW-OPENREDIRECT-01（`cflow-redirect-whitelist.md`） **[Inferred]** | 命中`VULN-CFLOW-OPENREDIRECT-01` | Python(urlparse)/Django(url_has_allowed_host_and_scheme)/Java(URI)/通用(相对路径) | 重定向目标白名单验证 | VULN-CFLOW-OPENREDIRECT-01 |
| FIX-CFLOW-IMPL-01（`cflow-correct-condition.md`） **[Inferred]** | 命中`VULN-CFLOW-IMPL-01` | C/C++(-Wall -Werror/Yoda)/Python(pylint)/Java(-Werror) | 修正条件表达式——正确比较运算符/启用警告 | VULN-CFLOW-IMPL-01 |
| FIX-CFLOW-ORDER-01（`cflow-correct-operation-order.md`） **[Inferred]** | 命中`VULN-CFLOW-ORDER-01` | Python(装饰器)/Java Spring(@PreAuthorize)/Node.js(中间件)/通用(前置检查) | 修正安全关键操作顺序——检查在前操作在后 | VULN-CFLOW-ORDER-01 |
| FIX-CFLOW-CALL-01（`cflow-correct-function-call.md`） **[Inferred]** | 命中`VULN-CFLOW-CALL-01` | Python(命名参数)/C/C++(-Wall/正确顺序)/Java(重载选择) | 修正函数调用参数匹配——命名参数/类型检查 | VULN-CFLOW-CALL-01 |
| FIX-CFLOW-SCOPE-01（`cflow-correct-scoping.md`） **[Inferred]** | 命中`VULN-CFLOW-SCOPE-01` | JavaScript(let/const)/Python(global/nonlocal)/Java(精确catch)/通用(最小作用域) | 修正作用域管理——最小作用域/let/精确catch | VULN-CFLOW-SCOPE-01 |
| FIX-CFLOW-WORKFLOW-01（`cflow-workflow-state-machine.md`） **[Inferred]** | 命中`VULN-CFLOW-WORKFLOW-01` | 通用(状态字段验证/状态机)/Python(transitions)/Java(Spring StateMachine) | 工作流步骤状态机强制——服务端状态跟踪 | VULN-CFLOW-WORKFLOW-01 |
| FIX-INFO-EXPOSURE-01（`info-field-level-filtering.md`） **[Inferred]** | 命中`VULN-INFO-EXPOSURE-01` | Python Django(exclude)/Java Spring(@JsonIgnore)/Node.js(白名单)/通用(错误脱敏) | 字段级访问控制——序列化白名单/错误脱敏/日志脱敏 | VULN-INFO-EXPOSURE-01 |
| FIX-INFO-OBSERVABLE-01（`info-behavior-normalization.md`） **[Inferred]** | 命中`VULN-INFO-OBSERVABLE-01` | Python(secrets.compare_digest)/Java(MessageDigest.isEqual)/通用(统一错误) | 行为归一化——统一错误/常量时间比较 | VULN-INFO-OBSERVABLE-01 |
| FIX-INFO-STORAGE-01（`info-encrypted-storage.md`） **[Inferred]** | 命中`VULN-INFO-STORAGE-01` | Python(cryptography/KMS)/Java(AWS Encryption SDK)/通用(KMS/文件权限/列加密) | 敏感数据加密存储——AES/KMS/列加密/最小权限 | VULN-INFO-STORAGE-01 |
| FIX-INFO-LOSS-01（`info-integrity-protection.md`） **[Inferred]** | 命中`VULN-INFO-LOSS-01` | Python(hmac)/Java(javax.crypto.Mac)/通用(拒绝超长/HSTS) | 信息完整性保护——HMAC/长度验证/安全头保护 | VULN-INFO-LOSS-01 |
| FIX-INFO-REMOVAL-01（`info-secure-data-removal.md`） **[Inferred]** | 命中`VULN-INFO-REMOVAL-01` | C(explicit_bzero)/C++(volatile fill)/Python(主动清除)/通用(shred/缓存TTL) | 敏感数据安全清除——覆盖内存/安全擦除/缓存TTL | VULN-INFO-REMOVAL-01 |
| FIX-INFO-LEAK-01（`info-cross-domain-filtering.md`） **[Inferred]** | 命中`VULN-INFO-LEAK-01` | 通用(自定义错误页面/DEBUG=False/字段过滤/路径白名单) | 跨域传输过滤——错误脱敏/内部地址过滤/路径白名单 | VULN-INFO-LEAK-01 |
| FIX-INFO-COVERT-01（`info-covert-channel-control.md`） **[Inferred]** | 命中`VULN-INFO-COVERT-01` | Python(secrets.compare_digest)/Java(MessageDigest.isEqual)/C(CRYPTO_memcmp)/通用(隔离/噪声) | 隐蔽信道控制——常量时间/资源隔离/噪声注入 | VULN-INFO-COVERT-01 |
| FIX-HW-MEMPROT-01（`hw-memory-protection-enforcement.md`） **[Inferred]** | 命中`VULN-HW-MEMPROT-01` | C/嵌入式固件/MMU/MPU配置 | 部署硬件内存保护——W^X/范围隔离/镜像校验/分配控制 | VULN-HW-MEMPROT-01 |
| FIX-HW-DEBUG-01（`hw-debug-interface-disable.md`） **[Inferred]** | 命中`VULN-HW-DEBUG-01` | IoT/嵌入式设备/SoC安全 | 生产环境禁用调试/测试接口——JTAG熔断/测试逻辑锁定 | VULN-HW-DEBUG-01 |
| FIX-HW-FIRMWARE-01（`hw-secure-firmware-update.md`） **[Inferred]** | 命中`VULN-HW-FIRMWARE-01` | IoT/嵌入式设备/SoC安全 | 部署安全固件更新机制——可写Flash+签名验证+OTA | VULN-HW-FIRMWARE-01 |
| FIX-HW-ROOT-01（`hw-immutable-root-of-trust.md`） **[Inferred]** | 命中`VULN-HW-ROOT-01` | C/嵌入式固件/eFuse/ROM/TPM | 部署不可变信任根存储——ROM/eFuse | VULN-HW-ROOT-01 |
| FIX-HW-LOGIC-01（`hw-logic-fault-handling.md`） **[Inferred]** | 命中`VULN-HW-LOGIC-01` | Verilog/VHDL/SoC设计 | 部署硬件逻辑故障处理——FSM错误状态/通道同步/指令故障检测 | VULN-HW-LOGIC-01 |
| FIX-HW-FABRIC-01（`hw-fabric-security-features.md`） **[Inferred]** | 命中`VULN-HW-FABRIC-01` | Verilog/VHDL/SoC/AXI/AHB | 部署片上总线安全特性——安全位/参数写保护/fabric防火墙 | VULN-HW-FABRIC-01 |
| FIX-HW-RE-01（`hw-reverse-engineering-protection.md`） **[Inferred]** | 命中`VULN-HW-RE-01` | IC设计/SoC安全/嵌入式安全 | 部署逆向工程防护——金属层遮挡/走线屏蔽/防拆解/探测传感器 | VULN-HW-RE-01 |
| FIX-CODE-DANGEROUS-01（`code-replace-dangerous-functions.md`） **[Inferred]** | 命中`VULN-CODE-DANGEROUS-01` | C/C++（gets→fgets/strcpy→strncpy/sprintf→snprintf） | 替换危险函数为安全替代——带边界检查的函数 | VULN-CODE-DANGEROUS-01 |
| FIX-CODE-DYNCTRL-01（`code-dynamic-control-whitelist.md`） **[Inferred]** | 命中`VULN-CODE-DYNCTRL-01` | Python(importlib)/Java(ClassLoader)/Node.js(require) | 部署动态代码白名单和验证——模块白名单/来源验证/完整性校验 | VULN-CODE-DYNCTRL-01 |
| FIX-CODE-EMBEDDED-01（`code-supply-chain-verification.md`） **[Inferred]** | 命中`VULN-CODE-EMBEDDED-01` | npm/PyPI/通用供应链 | 部署供应链验证——verified publisher/签名/哈希/依赖锁定 | VULN-CODE-EMBEDDED-01 |
| FIX-CODE-HIDDEN-01（`code-remove-hidden-functionality.md`） **[Inferred]** | 命中`VULN-CODE-HIDDEN-01` | Web/桌面/移动/通用 | 移除隐藏功能/禁用调试代码——不可绕过的环境检查 | VULN-CODE-HIDDEN-01 |
| FIX-CODE-PROHIBITED-01（`code-enforce-prohibited-usage-rules.md`） **[Inferred]** | 命中`VULN-CODE-PROHIBITED-01` | C/C++/Java/通用linter/CI | 部署禁用代码检测和阻止——linter/编译器警告/CI门控 | VULN-CODE-PROHIBITED-01 |
| FIX-CODE-SPECMISMATCH-01（`code-align-implementation-to-spec.md`） **[Inferred]** | 命中`VULN-CODE-SPECMISMATCH-01` | 不限语言/框架 | 对齐实现与规范并建立一致性验证——契约测试 | VULN-CODE-SPECMISMATCH-01 |
| FIX-CODE-UNDEF-01（`code-eliminate-undefined-behavior.md`） **[Inferred]** | 命中`VULN-CODE-UNDEF-01` | C/C++/Rust(unsafe)/通用编译器 | 消除未定义行为依赖——显式检查/volatile防优化/UBSan | VULN-CODE-UNDEF-01 |
| FIX-AI-PROMPTINJ-01（`ai-prompt-injection-isolation.md`） **[Inferred]** | 命中`VULN-AI-PROMPTINJ-01` | LLM应用(OpenAI/Anthropic/LangChain) | 部署提示输入隔离和安全护栏——结构化消息/指令层级/输出过滤 | VULN-AI-PROMPTINJ-01 |
| FIX-AI-ADVERSARIAL-01（`ai-adversarial-input-defense.md`） **[Inferred]** | 命中`VULN-AI-ADVERSARIAL-01` | ML框架(TensorFlow/PyTorch)/识别系统 | 部署对抗性输入检测和防御——对抗性检测/对抗性训练/置信度校验 | VULN-AI-ADVERSARIAL-01 |
| FIX-AI-CONFIG-01（`ai-secure-inference-parameters.md`） **[Inferred]** | 命中`VULN-AI-CONFIG-01` | LLM应用(OpenAI/Anthropic API) | 部署安全推理参数配置——温度上限/top_p限制/token限制 | VULN-AI-CONFIG-01 |
| FIX-AI-OUTPUT-01（`ai-output-validation-and-filtering.md`） **[Inferred]** | 命中`VULN-AI-OUTPUT-01` | LLM应用/代码生成/通用AI输出消费 | 部署AI输出验证和过滤——内容审核/AST验证/沙箱执行 | VULN-AI-OUTPUT-01 |
| FIX-AI-OPTIMIZATION-01（`ai-optimization-safety-verification.md`） **[Inferred]** | 命中`VULN-AI-OPTIMIZATION-01` | C/C++编译器/AI模型优化/自动调优 | 部署优化安全验证——volatile防优化/优化前后安全回归测试 | VULN-AI-OPTIMIZATION-01 |
| FIX-SPHERE-ISOLATION-01（`sphere-enforce-isolation.md`） **[Inferred]** | 命中`VULN-SPHERE-ISOLATION-01` | SaaS(RLS)/容器(namespace+cgroup)/Unix(chroot) | 部署隔离机制——租户数据过滤/namespace/cgroup/进程隔离 | VULN-SPHERE-ISOLATION-01 |
| FIX-SPHERE-ALTPATH-01（`sphere-protect-all-paths.md`） **[Inferred]** | 命中`VULN-SPHERE-ALTPATH-01` | Web/微服务/通用多路径系统 | 为所有访问路径部署一致的安全控制 | VULN-SPHERE-ALTPATH-01 |
| FIX-SPHERE-CHANNEL-01（`sphere-secure-channel.md`） **[Inferred]** | 命中`VULN-SPHERE-CHANNEL-01` | 不限语言/TLS/mTLS/HTTPS | 部署加密和认证的通信信道——TLS/mTLS/证书验证 | VULN-SPHERE-CHANNEL-01 |
| FIX-SPHERE-EXTINFLUENCE-01（`sphere-protect-domain-definition.md`） **[Inferred]** | 命中`VULN-SPHERE-EXTINFLUENCE-01` | K8s/云服务/Web配置 | 保护域定义配置——管理员限制/输入验证/完整性校验 | VULN-SPHERE-EXTINFLUENCE-01 |
| FIX-SPHERE-EXTREF-01（`sphere-validate-cross-domain-reference.md`） **[Inferred]** | 命中`VULN-SPHERE-EXTREF-01` | Web/API/OAuth/服务间通信 | 验证跨域资源引用——URL白名单/内网过滤/协议验证 | VULN-SPHERE-EXTREF-01 |
| FIX-SPHERE-TRANSFER-01（`sphere-secure-cross-domain-transfer.md`） **[Inferred]** | 命中`VULN-SPHERE-TRANSFER-01` | 微服务/API Gateway/通用跨域传输 | 部署安全跨域转移控制——目标域验证/数据过滤/脱敏 | VULN-SPHERE-TRANSFER-01 |
| FIX-SPHERE-EXPOSURE-01（`sphere-restrict-exposure-scope.md`） **[Inferred]** | 命中`VULN-SPHERE-EXPOSURE-01` | Web/K8s/云服务/通用服务暴露 | 限制资源暴露范围——监听地址限制/NetworkPolicy/安全组 | VULN-SPHERE-EXPOSURE-01 |
| FIX-UI-MISREP-01（`ui-display-actual-consistency.md`） **[Inferred]** | 命中`VULN-UI-MISREP-01` | 浏览器/邮件/Web/移动 | 确保UI显示与实际信息一致——链接一致/punycode检测 | VULN-UI-MISREP-01 |
| FIX-UI-WARNING-01（`ui-dangerous-operation-warning.md`） **[Inferred]** | 命中`VULN-UI-WARNING-01` | Web/桌面/移动 | 为危险操作部署警告提示——确认对话框/二次确认 | VULN-UI-WARNING-01 |
| FIX-UI-DISCREPANCY-01（`ui-security-state-consistency.md`） **[Inferred]** | 命中`VULN-UI-DISCREPANCY-01` | Web/移动/桌面 | 确保安全状态显示与实际行为一致——HTTPS指示器/安全开关 | VULN-UI-DISCREPANCY-01 |
| FIX-INTER-CONFUSED-01（`inter-deputy-permission-verification.md`） **[Inferred]** | 命中`VULN-INTER-CONFUSED-01` | 编译器/API Gateway/系统服务/特权服务 | 代理程序权限验证——执行特权操作前验证请求方权限 | VULN-INTER-CONFUSED-01 |
| FIX-INTER-INTERPCONFLICT-01（`inter-canonicalize-shared-interpretation.md`） **[Inferred]** | 命中`VULN-INTER-INTERPCONFLICT-01` | URL解析/编码/HTTP请求解析 | 统一规范化和共享解释——统一规范化/共享解析逻辑 | VULN-INTER-INTERPCONFLICT-01 |
| FIX-INTER-SPECVIOLATION-01（`inter-precondition-checking.md`） **[Inferred]** | 命中`VULN-INTER-SPECVIOLATION-01` | C/Rust/通用API/库接口 | 部署前置条件检查——参数检查/约束验证/调用顺序 | VULN-INTER-SPECVIOLATION-01 |
| FIX-SUPPLY-UNTRUSTWORTHY-01（`supply-component-trust-verification.md`） **[Inferred]** | 命中`VULN-SUPPLY-UNTRUSTWORTHY-01` | npm/PyPI/通用包管理 | 部署组件信任验证——verified publisher/provenance/签名/依赖锁定 | VULN-SUPPLY-UNTRUSTWORTHY-01 |
| FIX-SUPPLY-VULNDEP-01（`supply-update-vulnerable-dependencies.md`） **[Inferred]** | 命中`VULN-SUPPLY-VULNDEP-01` | npm/PyPI/通用SCA/Dependabot | 更新易受攻击的依赖组件——升级到已修复版本/SCA扫描/自动更新 | VULN-SUPPLY-VULNDEP-01 |
| FIX-STATE-EXTCONTROL-01（`state-field-whitelist.md`） **[Inferred]** | 命中`VULN-STATE-EXTCONTROL-01` | Web(mass assignment防护)/API/PHP | 部署状态字段白名单——外部输入只更新非关键字段 | VULN-STATE-EXTCONTROL-01 |
| FIX-STATE-INCOMPLETE-01（`state-explicit-enumeration.md`） **[Inferred]** | 命中`VULN-STATE-INCOMPLETE-01` | 状态机/认证框架/通用状态管理 | 部署显式状态枚举——枚举区分所有安全状态/转换矩阵 | VULN-STATE-INCOMPLETE-01 |
| FIX-PHYSICAL-ENV-01（`physical-environment-monitoring.md`） **[Inferred]** | 命中`VULN-PHYSICAL-ENV-01` | 硬件安全/IoT/嵌入式 | 部署环境条件监测——电压/温度监测/故障注入防护/安全状态 | VULN-PHYSICAL-ENV-01 |
| FIX-PHYSICAL-POWER-01（`physical-constant-power-execution.md`） **[Inferred]** | 命中`VULN-PHYSICAL-POWER-01` | 嵌入式/智能卡/硬件密码 | 部署恒定功耗执行——恒定时间/恒定功耗/功耗随机化 | VULN-PHYSICAL-POWER-01 |
| FIX-TYPE-CAST-01（`type-safe-cast-conversion.md`） **[Inferred]** | 命中`VULN-TYPE-CAST-01` | C/C++/Rust(TryFrom)/C++(narrowing)/编译器警告 | 使用安全类型转换——转换前范围检查/安全转换API | VULN-TYPE-CAST-01 |
| FIX-NAME-RESOLUTION-01（`name-secure-resolution.md`） **[Inferred]** | 命中`VULN-NAME-RESOLUTION-01` | Python(模块搜索)/DNS(DNSSEC)/通用名称解析 | 部署安全名称解析——绝对路径/路径完整性验证/DNSSEC | VULN-NAME-RESOLUTION-01 |
| FIX-PROCESS-CONTROL-01（`process-sandbox-permission.md`） **[Inferred]** | 命中`VULN-PROCESS-CONTROL-01` | OS/容器/通用进程管理 | 部署进程沙箱和权限限制——预定义命令/权限最小化/沙箱 | VULN-PROCESS-CONTROL-01 |
| FIX-LOGGING-INSUFFICIENT-01（`logging-security-event-logging.md`） **[Inferred]** | 命中`VULN-LOGGING-INSUFFICIENT-01` | Python(logging)/Java(SLF4J)/通用日志 | 部署安全事件日志记录——安全关键事件记录/审计日志 | VULN-LOGGING-INSUFFICIENT-01 |
| FIX-ENCAP-INSUFFICIENT-01（`encapsulation-proper-hiding.md`） **[Inferred]** | 命中`VULN-ENCAP-INSUFFICIENT-01` | Java(private/protected)/Python(_private)/通用OOP | 部署正确的封装和访问控制——private/protected/访问器/防御性复制 | VULN-ENCAP-INSUFFICIENT-01 |
| FIX-ENC-ENCODING-01（`encoding-context-aware-escaping.md`） **[Inferred]** | 命中`VULN-ENC-ENCODING-01` | Python(html.escape)/Java(OWASP Encoder)/通用模板 | 部署上下文感知的输出编码——HTML/JS/URL/CSS转义匹配上下文 | VULN-ENC-ENCODING-01 |
| FIX-AC-OWNERSHIP-01（`add-ownership-verification.md`） **[Inferred]** | 命中`VULN-AC-OWNERSHIP-01` | Web/API/多租户应用 | 资源操作前校验当前主体或租户所有权 | VULN-AC-OWNERSHIP-01 |
| FIX-AC-PERM-ASSIGN-01（`set-minimum-file-permissions.md`） **[Inferred]** | 命中`VULN-AC-PERM-ASSIGN-01` | Unix/Linux文件系统及跨平台文件API | 创建资源时显式设置最小权限并核实umask | VULN-AC-PERM-ASSIGN-01 |
| FIX-AC-PHYSICAL-01（`physical-access-controls.md`） **[Inferred]** | 命中`VULN-AC-PHYSICAL-01` | 硬件、IoT、嵌入式与终端设备 | 禁用或封装生产接口并部署防拆与访问控制 | VULN-AC-PHYSICAL-01 |
| FIX-AC-PRIVILEGE-01（`complete-privilege-dropping.md`） **[Inferred]** | 命中`VULN-AC-PRIVILEGE-01` | Unix/Linux系统编程与容器入口 | 按正确顺序完整放弃特权并检查返回值 | VULN-AC-PRIVILEGE-01 |
| FIX-AC-SESSION-REGEN-01（`regenerate-session-after-auth.md`） **[Inferred]** | 命中`VULN-AC-USERMGMT-01` | 有状态会话框架 | 认证成功和权限变化后重新生成会话标识符 | VULN-AC-USERMGMT-01 |
| FIX-AUTHN-COMPLETE-01（`complete-authentication-verification.md`） **[Inferred]** | 命中`VULN-AUTHN-BYPASS-01` | Web/API/桌面/移动认证流程 | 补齐凭证、状态和认证结果的完整验证逻辑 | VULN-AUTHN-BYPASS-01 |
| FIX-AUTHN-CRED-PROTECT-01（`secure-credential-storage-handling.md`） **[Inferred]** | 命中`VULN-AUTHN-CRED-PROTECT-01` | 所有凭证存储与处理流程 | 专用密码哈希、日志脱敏并禁止响应返回凭证 | VULN-AUTHN-CRED-PROTECT-01 |
| FIX-AUTHN-LOCKOUT-01（`balanced-lockout-policy.md`） **[Inferred]** | 命中`VULN-AUTHN-LOCKOUT-01` | 所有账户锁定实现 | 使用渐进延迟、合理阈值和多维限速避免锁定DoS | VULN-AUTHN-LOCKOUT-01 |
| FIX-AUTHN-PASSHASH-01（`reject-hash-as-credential.md`） **[Inferred]** | 命中`VULN-AUTHN-PASSHASH-01` | 自定义认证、遗留协议与API | 拒绝客户端哈希凭证，只在服务端验证原始凭证 | VULN-AUTHN-PASSHASH-01 |
| FIX-AUTHN-RATELIMIT-01（`add-rate-limiting-and-lockout.md`） **[Inferred]** | 命中`VULN-AUTHN-NO-RATELIMIT-01` | 所有认证端点 | 添加账号/IP维度限速、渐进延迟和合理锁定 | VULN-AUTHN-NO-RATELIMIT-01 |
| FIX-AUTHN-SECURE-ID-01（`use-csprng-for-identifiers.md`） **[Inferred]** | 命中`VULN-AUTHN-INSECURE-ID-01` | 会话与令牌系统 | 使用足够熵的CSPRNG生成不可预测标识符 | VULN-AUTHN-INSECURE-ID-01 |
| FIX-AUTHN-SESSION-LIFECYCLE-01（`proper-session-lifecycle-management.md`） **[Inferred]** | 命中`VULN-AUTHN-SESSION-LIFECYCLE-01` | 有状态会话与令牌系统 | 设置合理超时并在登出、改密等事件后服务端失效 | VULN-AUTHN-SESSION-LIFECYCLE-01 |
| FIX-AUTHN-WEAK-CRED-01（`enforce-strong-credential-policy.md`） **[Inferred]** | 命中`VULN-AUTHN-WEAK-CRED-01` | 所有认证与凭证配置场景 | 强制凭证强度并移除默认或硬编码凭证 | VULN-AUTHN-WEAK-CRED-01 |
| FIX-AUTHZ-OBJECT-LEVEL-01（`add-object-level-authorization.md`） **[Inferred]** | 命中`VULN-AUTHZ-OBJECT-LEVEL-01` | Web/API/ORM/多租户应用 | 对象查询和更新绑定当前主体或租户并校验所有权 | VULN-AUTHZ-OBJECT-LEVEL-01 |

## 3. 单个知识条目内部结构规范

**文件组织**：每个知识条目是独立小文件，复用#16已定的"小文件"哲学。分类粒度当前未定，条目数量较少时可直接放在`fix-patterns/`根目录下；增长到需要分类时，按第7节的规模应对方案拆分。

**模板**：编写新条目时参考 [`_template.md`](_template.md)（模板不计入正式知识条目，不构成检测能力）。

**内部结构**：仍以**Source / Propagation / Sanitizer / Sink**四段为骨架组织，对应#4已确立的六项验收基线字段——修复动作本质上是在这条链的某个环节上做加固，条目必须明确标注作用在哪个环节。2026-08-09知识建设批次（KBATCH-001）后，模板扩展为以下完整章节：

| 修复作用环节 | 典型修复动作 | 对应#4六项验收基线 |
|---|---|---|
| 收紧Source | 输入白名单校验、类型强制、来源身份校验 | 削弱可控性（controllable） |
| 切断Propagation | 移除不必要的数据传递路径、增加边界隔离 | 削弱可达性/传播完整性（reachable / propagatable） |
| 补齐/加固Sanitizer | 参数化查询、编码转义、反序列化白名单——最常见的修复作用点 | 恢复传播完整性（propagatable） |
| 加固Sink本身 | 最小权限、沙箱化危险操作、二次确认 | 削弱可利用性/降低影响（exploitable / impact） |

条目还必须记录该修复动作**如何验证生效**——复用#7已确立的验证方式（复用`exploit-proof`已建立的PoC/复现手段重新跑一遍确认原漏洞不再触发），以及**是否可能破坏合法行为/兼容性**（#7优先级顺序第3项"合法行为/兼容性保留"要求，条目应老实标注该修复动作常见的兼容性副作用，供#7引用时提前预判）。

## 4. 强制显式查阅纪律（核心纪律，不得含糊）

- "要不要查、查了没有"不能交给#7自由裁量。#7窄范围战术修复消费本目录时，产出必须显式写明**查了哪个条目ID**（对应`remediation-guidance/SKILL.md`已落地的`fix_pattern_ref`字段要求）。
- 查不到匹配条目时，必须显式写**"未匹配，本次修复为个案定制，未套用标准fix-pattern"**，不能含糊过去或默默跳过不提。
- 引用的条目ID必须可被机械核对——是否真实存在于本索引表格里（应用#17已确立的T2机械核对能力）。核对对象是"引用的ID是否存在"这件事本身，不涉及"套用这条修复对不对"，后者仍是#7自己按优先级顺序判断的职责。核对由宿主Agent按#17 T2机械核对能力执行——检查ID是否存在于本索引表格中即可，不需要GenSource自建验证程序。

## 5. 引用分级

复用#7/#11已确立的**Observed / Inferred / Proposed**三段式标签，不新造标签体系。在本目录场景下的含义需要区分"条目本身的默认分级"与"某次具体引用的分级"两层——这两层可能不同（条目本身可能是Observed，但套用到某次具体代码上因存在细节差异只能标Inferred），索引/条目文件只承载第一层，第二层始终由#7每次引用时独立判断：

- **Observed**：该修复模式已在多个已确认修复案例中实际套用并验证生效，效果稳定。
- **Inferred**：从其他来源（如CWE官方修复建议、语言/框架官方文档）转译得出，尚未在本项目实际验证案例中套用过。
- **Proposed**：条目本身来自尚未充分验证的新增知识（例如持续学习流程产出但尚未经人工复核的条目）。

**标注归属**：条目文件/索引记录的是条目本身的默认分级；#7实际引用某条目产出补丁时，其`evidence_tag`字段（`remediation-guidance/SKILL.md`已有此字段）由#7根据"这次具体修复"重新独立判断，不能直接继承条目默认标签、不能省略这次独立判断。

## 6. 不采纳向量/混合检索

复用06号早期跨竞品打分框架已确立、24号（#15）再次确认仍有效的结论：**F1（纯Markdown小文件+表格索引）为基座不动摇，F2（向量/混合检索）明确不采纳**。

**元星刃反例**（06号/24号已引用）：元星刃建成了CWE-7全量XML+BM25/Chroma混合检索能力，但8个worker的system prompt完全没有引用检索结果——"知识库与审计流程完全脱钩"（`09-yuanxingren.md`§9）。这证明"有检索能力"和"检索能力真正驱动判断"是两件不同的事，不能想当然认为"上了向量库就变强"。

本目录索引同样始终保持"表格化+扫一眼就能判断该不该细看"的哲学，不引入语义相似度检索或混合检索基础设施。

## 7. 索引规模过大时的应对

复用#12（`docs/research/decision/25-category12-scale-cost-management-spec.md`第4节）已确认的方案：**索引本身分层拆分成"子类索引+索引的索引"，不引入向量检索**。

- 当本文件这一份表格本身也大到难以被"扫一眼"评估时，按分类维度（如按对应vuln-pattern的CWE大类、按语言/框架，具体分类维度留待实际条目积累后确定）拆出`fix-patterns/<category>/_index.md`子类索引，每份子类索引仍是同样的表格格式（第2节列定义不变）。
- 拆分后，本文件（`fix-patterns/_index.md`）升级为"索引的索引"——只列每个子类索引的名称/条目数量概览/相对路径链接。
- **语言覆盖度老实披露**（复用#13已确立原则）：修复动作的具体实现天然语言相关，按语言/框架拆分后若某语言条目数量明显偏少，#7引用时必须显式披露完整性置信度较低，不能装作深度一致；无标准fix-pattern覆盖的语言，应回落为按#4六项基线原则手工定制修复（个案定制），不得强行套用其他语言的修复模式。
- **中文文本匹配caveat**（复用#13已披露的LANG-04）：若"触发信号"或摘要涉及中文文本匹配，标准按空格分词的正则匹配对中文不生效，需要单独处理，具体方式留待实际编写时确定。

## 8. 待办声明

分类粒度、条目文件具体命名规则、机械核对的具体实现，均留待未来实际编写知识条目/contracts层设计时确定，本文件不提前杜撰。
