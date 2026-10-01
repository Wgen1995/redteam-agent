# 汇点类别索引（sinks/_index.md）

> 来源：docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md（安全本体与行业漏洞全集实现计划）任务3；docs/research/28-detection-engine-design.md §9 知识层配套（双轨索引补全）。本文件是汇点类别索引，容纳 Sink、State Transition、Resource Consumption 三个子类，按 **OWASP Top 10（A01–A10）× CWE Top 25 2024** 双轨组织，每类给出跨语言识别信号。

> **禁止名称映射推导检测能力**：本表只是**识别信号目录**——列出的 grep 模式用于预筛分流，不构成检测结论。某类的 discoverable 列以 vuln-patterns/ 是否实际存在可执行发现条目为准，并如实标注；无对应条目的类只能识别信号、不能声称可发现。

## 索引格式

| 列名 | 含义 |
|---|---|
| stable_id | 稳定ID |
| name | 名称 |
| ontology_ref | 本体引用（ONT-SINK / ONT-STATE-TRANSITION / ONT-RESOURCE-CONSUMPTION） |
| owasp | OWASP Top 10 2021 归入项（A01–A10；跨类安全属性另列） |
| cwe | CWE 引用（以 CWE Top 25 2024 为主，附相关 CWE） |
| recognition_signals | 跨语言识别信号（Py=Python / J=Java / N=Node.js / PHP=PHP / Go=Go 的 grep 模式；双兼容 ERE 子集，不用词边界转义） |
| related_semantics | 关联统一漏洞语义（UVS-*）与 vuln-patterns 条目 |
| discoverable | 是否有对应可执行发现条目（以 vuln-patterns 实际条目为准） |

> **信号分级（2026-08-14 实跑新增）**：实例级信号=命中进 sink_inventory 逐条成检查点；**信号级（噪声级）**=命中只作为浅扫过滤条件与线索，不逐条进 sink_inventory（避免 5 万+ 检查点假账本）。当前信号级类：SINK-SENSITIVE-EXPOSE（printStackTrace/getMessage 类，25k+ 命中）、SINK-LOGGING-INSUFF、SINK-AUTHN-BYPASS、SINK-BRUTE-FORCE、SINK-OBSERVABLE-DIFF、SINK-STATE-CONCURRENT（synchronized 全量命中）、SINK-MEM-INDEX（get/charAt 类）。上述信号级类在 coverage/semantic-capability 分片中的 discoverable 标注为“信号级（不进实例清单）”而非 complete，与“不入 sink_inventory”口径一致。
>
> **语言覆盖诚实声明（2026-08-13）**：本表识别信号当前覆盖 5 种语言（Py/J/N/PHP/Go）；设计 §9.1 的 15 语言目标中，C/C++/C#/Ruby/Rust/Kotlin/Swift/Scala/Groovy/PowerShell 尚未落地，如实标注 not_started，不声称覆盖。
> **八段规则知识承载方式（实现裁决）**：设计 §9.1 的"每个 sink_type 一个 8 段规则文件"由 vuln-patterns 条目承载（148 条目内含前置/Source/Sink/Propagation/Sanitizer/Disproof/CWE 映射/修复引用各段），本表 related_semantics 列映射到具体条目，不另建重复规则文件，避免两份知识漂移。
| source_refs | 来源引用 |
| version | 版本 |

## A01 失效的访问控制（Broken Access Control）

| stable_id | name | ontology_ref | owasp | cwe | recognition_signals | related_semantics | discoverable | source_refs | version | grep_patterns |
|---|---|---|---|---|---|---|---|---|---|---|
| SINK-SQL-EXEC | SQL执行 | ONT-SINK | A03 | CWE-89 | Py: execute( / executemany( · J: executeQuery( / executeUpdate( / createStatement( / Statement.execute( · N: query( / execute( · PHP: ->query( / mysqli_query( · Go: db.Query( / db.Exec( | UVS-INJ-QUERY-INJECTION（sql-injection-string-concat.md） | 是 | 内部推导 | v0.2 | J:executeQuery|executeUpdate|createStatement N:query\(|execute\( Py:execute\(|executemany Go:db.Query|db.Exec |
| SINK-AUTHZ-MISSING | 缺失授权检查 | ONT-SINK | A01 | CWE-862 | Py: @login_required / @permission_required 部分路由缺失 · J: @PreAuthorize 缺失 · N: 中间件链缺失 app.use(auth) · PHP: $this->auth 未调用 · Go: middleware.Auth 未装配 | UVS-AC-AUTHORIZATION-FAILURE（missing-authorization-check.md） | 是 | 内部推导 | v0.2 |
| SINK-OBJECT-AUTHZ | 对象级授权缺失(IDOR) | ONT-SINK | A01 | CWE-862/639 | Py: get_object_or_404 未校验 owner · J: findById 未绑定主体 · N: findById 未绑定 req.user · PHP: find( 未校验 owner · Go: db.First 未校验 owner | UVS-AC-AUTHORIZATION-FAILURE（object-level-authorization-missing.md） | 是 | 内部推导 | v0.2 |
| SINK-CSRF-ORIGIN | 状态变更未验证来源(CSRF) | ONT-SINK | A01 | CWE-352/346/940 | Py: @csrf_exempt / 缺 CSRFProtect · J: 缺 CSRFFilter · N: 缺 csurf · PHP: 缺 token 校验 · Go: POST 路由无 origin 校验 | UVS-AC-AUTHORIZATION-FAILURE（missing-origin-validation.md） | 是 | 内部推导 | v0.2 |
| SINK-PRIV-DROP | 权限放弃不完整 | ONT-STATE-TRANSITION | A01 | CWE-269 | Py: setuid( / setgid( · J: doPrivileged · N: process.setuid · PHP: posix_setuid · Go: syscall.Setuid | UVS-AC-PRIVILEGE-MANAGEMENT-FAILURE（improper-privilege-dropping.md） | 是 | 内部推导 | v0.2 |
| SINK-PERM-ASSIGN | 默认权限过宽 | ONT-STATE-TRANSITION | A05 | CWE-276/732 | Py: os.chmod( / 0o777 · J: PosixFilePermission 过宽 · N: fs.chmod · PHP: chmod( · Go: os.Chmod / 0666 | UVS-AC-PERMISSION-ASSIGNMENT-ERROR（overly-permissive-default-permissions.md） | 是 | 内部推导 | v0.2 |
| SINK-MISSING-CHECK | 缺失边界检查（两段式：来源段+使用点段） | ONT-SINK | A01 | CWE-20 | Py: follow_symlinks / Content-Length / _directory_as_html / text/html · J: followLinks / Content-Length · N: content-length / Content-Length · Go: FollowSymlinks / ContentLength | UVS-INPUT-VALIDATION-FAILURE（input-validation-failure.md） | 是 | v0.11.3 | v0.11.3 | Py:follow_symlinks|Content-Length|_directory_as_html|text/html J:followLinks|Content-Length N:content-length|Content-Length Go:FollowSymlinks|ContentLength |
| SINK-FILE-TRAVERSAL | 路径穿越 | ONT-SINK | A01 | CWE-22 | Py: open( + 用户路径 · J: new File( + 用户路径 · N: fs.readFile( + 用户路径 · PHP: include / file_get_contents + 用户路径 · Go: os.Open( + 用户路径 | UVS-FILE-PATH-TRAVERSAL（file-path-traversal.md） | 是 | 内部推导 | v0.2 | J:new File|FileInputStream|Paths.get N:fs.readFile|path.join Py:open\(|os.path.join Go:os.Open Py:follow_symlinks Go:FollowSymlinks J:followLinks |
| SINK-OPEN-REDIRECT | 开放重定向 | ONT-SINK | A01 | CWE-601 | Py: redirect( + request.args · J: sendRedirect( + 参数 · N: res.redirect( + req.query · PHP: header(Location:) + $_GET · Go: http.Redirect + r.URL.Query | UVS-CFLOW-OPEN-REDIRECT（cflow-open-redirect.md） | 是 | 内部推导 | v0.2 | J:sendRedirect|RedirectView N:res.redirect Py:redirect\( Go:http.Redirect |

## A02 加密失败（Cryptographic Failures）

| stable_id | name | ontology_ref | owasp | cwe | recognition_signals | related_semantics | discoverable | source_refs | version | grep_patterns |
|---|---|---|---|---|---|---|---|---|---|---|
| SINK-WEAK-HASH | 弱哈希密码存储 | ONT-SINK | A02 | CWE-916/326 | Py: hashlib.md5( / sha1( · J: MessageDigest.getInstance(MD5) · N: createHash(md5) · PHP: md5( / sha1( · Go: md5.Sum | UVS-CRYPTO-WEAK-ALGORITHM（weak-unsalted-password-hash.md） | 是 | 内部推导 | v0.2 | J:MessageDigest.getInstance\(|MD5|SHA-1 N:createHash\( Py:hashlib.md5|hashlib.sha1 Go:md5.Sum|sha1.Sum |
| SINK-WEAK-CRYPTO-PARAM | 弱加密强度参数 | ONT-SINK | A02 | CWE-327/326 | Py: RSA.generate(1024) · J: Cipher(AES) 弱 keySize · N: createCipher(aes-128-ecb) · PHP: MCRYPT / DES · Go: rsa.GenerateKey(1024) | UVS-CRYPTO-WEAK-STRENGTH（weak-crypto-strength-params.md） | 是 | 内部推导 | v0.2 |
| SINK-CLEARTEXT | 敏感数据明文传输/存储 | ONT-SINK | A02 | CWE-311/312/319 | Py: http:// / verify=False · J: InsecureSkipVerify · N: rejectUnauthorized:false · PHP: CURLOPT_SSL_VERIFYPEER,false · Go: InsecureSkipVerify: true | UVS-CRYPTO-MISSING-ENCRYPTION（missing-encryption-cleartext.md） | 是 | 内部推导 | v0.2 |
| SINK-HARDCODED-CRED | 硬编码凭据 | ONT-SINK | A02 | CWE-798 | Py: password= / API_KEY= 常量 · J: private static final String PASSWORD · N: process.env 未用 · PHP: $password = · Go: const apiKey = | UVS-INFO-INSECURE-STORAGE（info-insecure-storage.md） | 是 | 内部推导 | v0.2 | J:private static final String PASSWORD|API_KEY= Py:password=|api_key= N:process.env |
| SINK-WEAK-RNG | 非CSPRNG随机 | ONT-SINK | A02 | CWE-330 | Py: random.rand / random.choice · J: java.util.Random · N: Math.random() · PHP: rand( / mt_rand( · Go: math/rand | UVS-CRYPTO-INSUFFICIENT-RANDOMNESS（insufficient-randomness-noncsprng.md） | 是 | 内部推导 | v0.2 | J:java.util.Random|Math.random N:Math.random\( Py:random.rand Go:math/rand |
| SINK-NO-AUTH-VERIFY | 缺失真实性验证 | ONT-SINK | A02 | CWE-345 | Py: verify=False / 未验签名 · J: 未验证书链 · N: rejectUnauthorized:false · PHP: CURLOPT_SSL_VERIFYPEER,false · Go: InsecureSkipVerify | UVS-CRYPTO-AUTHENTICITY-VERIFICATION-FAILURE（missing-authenticity-verification.md） | 是 | 内部推导 | v0.2 |
| SINK-KEY-NONCE-REUSE | 密钥/nonce重用 | ONT-SINK | A02 | CWE-323/330 | Py: 固定 iv / nonce · J: 固定 IvParameterSpec · N: 固定 iv · PHP: 固定 $iv · Go: 固定 nonce | UVS-CRYPTO-KEY-LIFECYCLE-FAILURE（key-lifecycle-nonce-reuse.md） | 是 | 内部推导 | v0.2 |
| SINK-MISSING-MAC | 加密缺MAC/AEAD | ONT-SINK | A02 | CWE-311 | Py: AES.MODE_CBC 无 MAC · J: Cipher(AES/CBC) · N: createCipher · PHP: mcrypt CBC · Go: cipher.NewCBCEncrypter 无 HMAC | UVS-CRYPTO-MISSING-STEP（missing-crypto-step-mac.md） | 是 | 内部推导 | v0.2 |

## A03 注入（Injection）

| stable_id | name | ontology_ref | owasp | cwe | recognition_signals | related_semantics | discoverable | source_refs | version | grep_patterns |
|---|---|---|---|---|---|---|---|---|---|---|
| SINK-CMD-EXEC | OS命令执行 | ONT-SINK | A03 | CWE-78 | Py: os.system( / os.popen( / subprocess.run( / subprocess.Popen( / subprocess.call( / check_output( / shell=True · J: Runtime.exec( / ProcessBuilder · N: child_process.exec( / execSync · PHP: system( / exec( / shell_exec( · Go: exec.Command / syscall.Exec | UVS-INJ-COMMAND-INJECTION（inj-command-injection.md） | 是 | 内部推导 | v0.2 | J:Runtime.getRuntime\(\)|ProcessBuilder|\.exec\( N:child_process.exec|execSync Py:os.system|os.popen|subprocess.run Go:exec.Command |
| SINK-CODE-EXEC | 动态代码执行 | ONT-SINK | A03 | CWE-94 | Py: eval( / exec( · J: ScriptEngine.eval / GroovyShell · N: eval( / new Function( · PHP: eval( / assert( · Go: （无原生 eval，注意 plugin/反射） | UVS-INJ-CODE-INJECTION（inj-code-injection.md） | 是 | 内部推导 | v0.2 |
| SINK-XSS-AUTOESCAPE | 模板自动转义关闭(XSS) | ONT-SINK | A03 | CWE-79 | Py: autoescape=False / | safe · J: th:utext · N: {{{...}}} 三括号 · PHP: {{ raw }} Twig · Go: template.HTML | UVS-INJ-XSS（template-autoescape-disabled-xss.md） | 是 | 内部推导 | v0.2 |
| SINK-XSS-RAWOUTPUT | 原生输出XSS | ONT-SINK | A03 | CWE-79 | Py: print( 未转义 · J: out.println( 未转义 · N: res.send( + HTML · PHP: echo 未 htmlspecialchars · Go: fmt.Fprintf(w,...) 未转义 | UVS-INJ-XSS（raw-output-no-escaping-xss.md） | 是 | 内部推导 | v0.2 |
| SINK-SSTI | 模板注入(SSTI) | ONT-SINK | A03 | CWE-1336 | Py: render_template_string( + 用户输入 · J: Velocity/FreeMarker 模板拼接 · N: ejs.render( + 用户输入 · PHP: render( + 用户输入 · Go: template.New + 用户输入 | （无专用 vuln-pattern；与 XSS-AUTOESCAPE 相关） | 否 | 内部推导 | v0.2 | J:Velocity|FreeMarker|Thymeleaf N:render\(|ejs Py:render_template_string Go:template.Execute |
| SINK-DESERIALIZE | 反序列化 | ONT-SINK | A03 | CWE-502 | Py: pickle.loads( / yaml.load( · J: ObjectInputStream.readObject / XMLDecoder / enableDefaultTyping · N: node-serialize / serialize · PHP: unserialize( · Go: gob.NewDecoder | UVS-INJ-DESERIALIZATION（inj-deserialization.md） | 是 | 内部推导 | v0.2 | J:ObjectInputStream|XMLDecoder|readObject N:node-serialize|serialize Py:pickle.loads|yaml.load Go:gob.NewDecoder |
| SINK-XXE | XML外部实体 | ONT-SINK | A03 | CWE-611 | Py: lxml.etree 未禁实体 · J: DocumentBuilderFactory 未禁 DTD · N: xml2js 无保护 · PHP: simplexml_load_string / LIBXML_NOENT · Go: xml.Decoder 未禁实体 | UVS-INJ-XXE（inj-xxe.md） | 是 | 内部推导 | v0.2 | J:DocumentBuilderFactory|SAXParserFactory|XMLReader Py:lxml.etree|simplexml_load_string Go:xml.Decoder |
| SINK-LDAP-QUERY | LDAP查询注入 | ONT-SINK | A03 | CWE-90 | Py: ldap.search( + 拼接 filter · J: DirContext.search( + 拼接 · N: ldapjs search + 拼接 · PHP: ldap_search( + 拼接 · Go: ldap.Search + 拼接 | （无专用 vuln-pattern；相关 inj-neutralization-failure.md） | 否 | 内部推导 | v0.2 |
| SINK-XPATH-QUERY | XPath查询注入 | ONT-SINK | A03 | CWE-643 | Py: etree.XPath( + 拼接 · J: XPath.evaluate + 拼接 · N: xpath + 拼接 · PHP: DOMXPath->query + 拼接 · Go: 少见 | （无专用 vuln-pattern；相关 inj-neutralization-failure.md） | 否 | 内部推导 | v0.2 |
| SINK-CRLF | CRLF/响应头注入 | ONT-SINK | A03 | CWE-93 | Py: header= + 用户值 · J: setHeader + 用户值 · N: res.setHeader + 用户值 · PHP: header( + 用户值 · Go: w.Header().Set + 用户值 | UVS-INJ-CRLF（inj-crlf-injection.md） | 是 | 内部推导 | v0.2 | J:setHeader|addHeader N:res.setHeader Py:header= Go:Header\(\)\.Set |
| SINK-FORMAT-STRING | 格式字符串 | ONT-SINK | A03 | CWE-134 | Py: % + 用户输入作格式 · J: String.format + 用户格式 · N: util.format + 用户格式 · PHP: printf( + 用户格式 · Go: fmt.Printf + 用户格式 | UVS-INJ-FORMAT-STRING（inj-format-string.md） | 是 | 内部推导 | v0.2 |
| SINK-RESOURCE-INJ | 资源标识符注入 | ONT-SINK | A03 | CWE-99 | Py: open( / include + 用户路径 · J: new File / ClassLoader + 用户 · N: require( + 用户 · PHP: include + 用户 · Go: os.Open + 用户 | UVS-INJ-RESOURCE-INJECTION（inj-resource-injection.md） | 是 | 内部推导 | v0.2 |
| SINK-SPECIAL-ELEM | 特殊元素未中和 | ONT-SINK | A03 | CWE-77 | Py: 日志/CSV/EL 拼接 · J: EL 求值 · N: 模板/日志拼接 · PHP: 日志拼接 · Go: 模板/日志拼接 | UVS-INJ-SPECIAL-ELEMENT-FAILURE（inj-special-element-failure.md） | 是 | 内部推导 | v0.2 |

## A04 不安全设计 & A05 安全配置错误

| stable_id | name | ontology_ref | owasp | cwe | recognition_signals | related_semantics | discoverable | source_refs | version | grep_patterns |
|---|---|---|---|---|---|---|---|---|---|---|
| SINK-SENSITIVE-EXPOSE | 敏感信息暴露 | ONT-SINK | A04 | CWE-200 | Py: to_dict() 含敏感字段 / 堆栈回显 · J: printStackTrace · N: res.send(err) · PHP: print_r($e) · Go: fmt.Println(err) 含内部路径 | UVS-INFO-SENSITIVE-EXPOSURE（info-sensitive-exposure.md） | 是 | 内部推导 | v0.2 |
| SINK-OBSERVABLE-DIFF | 可观察差异(侧信道) | ONT-SINK | A04 | CWE-209/203 | Py: 认证分支返回差异信息 · J: 常量时间比较缺失 · N: 认证分支差异 · PHP: == 比较密码 · Go: 非 subtle.ConstantTimeCompare | UVS-INFO-OBSERVABLE-DISCREPANCY（info-observable-discrepancy.md） | 是 | 内部推导 | v0.2 |
| SINK-FILE-UPLOAD | 无限制文件上传 | ONT-SINK | A05 | CWE-434 | Py: save( 未校验类型 · J: transferTo 未校验 · N: multer 未 filter · PHP: move_uploaded_file 未校验 · Go: io.Copy 未校验 | （无专用 vuln-pattern） | 否 | 内部推导 | v0.2 | J:transferTo|MultipartFile Py:save\(|upload N:multer Go:io.Copy |
| SINK-DEAD-CONTROL | 死安全控制 | ONT-SINK | A05 | CWE-（无独立编号） | Py: 中间件被注释 · J: Filter 未注册 · N: 中间件未 app.use · PHP: 校验函数未调用 · Go: middleware 未装配 | UVS-PROT-ADMIN-CONTROL-FAILURE（dead-security-control.md） | 是 | 内部推导 | v0.2 |

## A06 脆弱与过时组件

| stable_id | name | ontology_ref | owasp | cwe | recognition_signals | related_semantics | discoverable | source_refs | version | grep_patterns |
|---|---|---|---|---|---|---|---|---|---|---|
| SINK-VULN-DEP | 依赖含已知漏洞 | ONT-SINK | A06 | CWE-1104 | Py: requirements.txt 旧版本 · J: pom.xml 旧版本 · N: package.json 旧版本 · PHP: composer.json 旧版本 · Go: go.mod 旧版本 | UVS-SUPPLY-VULNERABLE-DEPENDENCY（supply-vulnerable-dependency.md） | 是 | 内部推导 | v0.2 |
| SINK-UNTRUST-COMPONENT | 不可信组件 | ONT-SINK | A06 | CWE-1357 | Py: 未签名包 · J: 未验 provenance · N: 非 verified publisher · PHP: 未验签名 · Go: 未验 sumdb | UVS-SUPPLY-UNTRUSTWORTHY-COMPONENT（supply-untrustworthy-component.md） | 是 | 内部推导 | v0.2 |

## A07 身份识别与认证失败

| stable_id | name | ontology_ref | owasp | cwe | recognition_signals | related_semantics | discoverable | source_refs | version | grep_patterns |
|---|---|---|---|---|---|---|---|---|---|---|
| SINK-AUTHN-BYPASS | 认证绕过 | ONT-SINK | A07 | CWE-287 | Py: 密码校验缺失/条件错误 · J: 认证结果未消费 · N: 认证结果未消费 · PHP: == 弱比较 · Go: 认证逻辑错误 | UVS-AUTHN-FAILURE（authentication-bypass.md） | 是 | 内部推导 | v0.2 |
| SINK-WEAK-CRED | 弱凭据策略 | ONT-STATE-TRANSITION | A07 | CWE-521 | Py: 密码长度/复杂度校验缺失 · J: 未校验强度 · N: 未校验强度 · PHP: 未校验强度 · Go: 未校验强度 | UVS-AUTHN-WEAK-CREDENTIALS（weak-credential-policy.md） | 是 | 内部推导 | v0.2 |
| SINK-SESSION-FIX | 会话固定 | ONT-STATE-TRANSITION | A07 | CWE-384 | Py: 登录后未 cycle_key · J: 未 changeSessionId · N: 未 regenerate · PHP: 未 session_regenerate_id · Go: 未重发 session | UVS-AC-USER-MANAGEMENT-ERROR（session-fixation-user-confusion.md） | 是 | 内部推导 | v0.2 |
| SINK-PREDICT-SESSION | 可预测会话ID | ONT-STATE-TRANSITION | A07 | CWE-330/331 | Py: 自增/时间戳 token · J: 自增 token · N: 自增 token · PHP: uniqid · Go: 自增 token | UVS-AUTHN-INSECURE-ID-MECHANISM（predictable-session-identifier.md） | 是 | 内部推导 | v0.2 |
| SINK-CRED-PLAINTEXT | 凭证明文存储 | ONT-SINK | A07 | CWE-256/312 | Py: 明文密码入库 · J: 明文密码 · N: 明文密码 · PHP: 明文密码 · Go: 明文密码 | UVS-AUTHN-CREDENTIAL-PROTECTION-FAILURE（plaintext-credential-storage.md） | 是 | 内部推导 | v0.2 |
| SINK-BRUTE-FORCE | 无暴力破解防护 | ONT-SINK | A07 | CWE-307 | Py: 登录端点无限速 · J: 无限速 · N: 无 rate-limit · PHP: 无限速 · Go: 无限速 | UVS-AUTHN-BRUTE-FORCE-FAILURE（missing-brute-force-protection.md） | 是 | 内部推导 | v0.2 |

## A08 软件与数据完整性失败

| stable_id | name | ontology_ref | owasp | cwe | recognition_signals | related_semantics | discoverable | source_refs | version | grep_patterns |
|---|---|---|---|---|---|---|---|---|---|---|
| SINK-NO-INTEGRITY | 更新/依赖未验完整性 | ONT-SINK | A08 | CWE-345/494 | Py: 下载未验 hash · J: 未验签名 · N: 未验 integrity · PHP: 未验签名 · Go: 未验 go.sum | UVS-CRYPTO-AUTHENTICITY-VERIFICATION-FAILURE（missing-authenticity-verification.md） | 是 | 内部推导 | v0.2 |
| SINK-PREDICT-ID | 可预测标识符 | ONT-SINK | A08 | CWE-330/340 | Py: 自增主键作公开ID · J: 自增ID · N: 自增ID · PHP: 自增ID · Go: 自增ID | UVS-CRYPTO-PREDICTABLE-IDENTIFIER（predictable-identifier-generation.md） | 是 | 内部推导 | v0.2 |

## A09 安全日志与监控失败

| stable_id | name | ontology_ref | owasp | cwe | recognition_signals | related_semantics | discoverable | source_refs | version | grep_patterns |
|---|---|---|---|---|---|---|---|---|---|---|
| SINK-LOGGING-INSUFF | 日志记录不足 | ONT-SINK | A09 | CWE-778 | Py: 认证/授权操作无 logging · J: 无 log · N: 无日志 · PHP: 无日志 · Go: 无日志 | UVS-LOGGING-INSUFFICIENT（logging-insufficient.md） | 是 | 内部推导 | v0.2 |

## A10 服务端请求伪造（SSRF）

| stable_id | name | ontology_ref | owasp | cwe | recognition_signals | related_semantics | discoverable | source_refs | version | grep_patterns |
|---|---|---|---|---|---|---|---|---|---|---|
| SINK-NET-REQUEST | 服务端网络请求(SSRF) | ONT-SINK | A10 | CWE-918 | Py: requests.get( + 用户URL · J: HttpClient / URLConnection + 用户URL · N: axios / fetch + 用户URL · PHP: curl_exec + 用户URL · Go: http.Get / http.NewRequest + client.Do + 用户URL | UVS-INJ-SSRF（inj-ssrf.md） | 是 | 内部推导 | v0.2 | J:URLConnection|HttpClient|openConnection N:axios|fetch\( Py:requests.get|urlopen Go:http.Get |
| SINK-H2-FLOW | HTTP/2 流控/帧大小校验（CVE-2020-11996 类） | ONT-RESOURCE-CONSUMPTION | A05 | CWE-770 | J: Http2UpgradeHandler / StreamStateMachine / windowUpdate / maxFrameSize / settings · Go: http2.Framer / MaxReadFrameSize · N: http2 session 实现 | （无专用 vuln-pattern） | 否 | 内部推导 | v0.2 | J:Http2UpgradeHandler|StreamStateMachine|windowUpdate|maxFrameSize |
| SINK-WS-FRAME | WebSocket 帧载荷长度校验（CVE-2020-13935 类） | ONT-RESOURCE-CONSUMPTION | A05 | CWE-770 | J: WsFrameBase / onData / payloadLength / maxBinaryMessageBufferSize · N: ws 帧解析 · Go: websocket 帧读取 | （无专用 vuln-pattern） | 否 | 内部推导 | v0.2 | J:WsFrameBase|payloadLength|maxBinaryMessageBufferSize |

## 跨类：内存安全（CWE Top 25 2024）

| stable_id | name | ontology_ref | owasp | cwe | recognition_signals | related_semantics | discoverable | source_refs | version | grep_patterns |
|---|---|---|---|---|---|---|---|---|---|---|
| SINK-MEM-BOUNDS | 越界写/缓冲区溢出 | ONT-SINK | 跨类 | CWE-787/119 | Py: ctypes memcpy · J: Unsafe · N: Buffer 越界 · PHP: 少见 · Go: unsafe slice · C: memcpy( / strcpy( / sprintf( | UVS-MEM-BOUNDS-FAILURE（mem-bounds-failure.md） | 是 | 内部推导 | v0.2 |
| SINK-MEM-INDEX | 越界读/索引越界 | ONT-SINK | 跨类 | CWE-125 | Py: arr[index] 未查界 · J: Unsafe · N: arr[index] · PHP: 少见 · Go: slice[i] · C: arr[index] | UVS-MEM-INDEX-ACCESS-ERROR（mem-index-access-error.md） | 是 | 内部推导 | v0.2 |
| SINK-UAF | 释放后使用 | ONT-SINK | 跨类 | CWE-416 | Py/J/N/PHP/Go: 少见 · C: free( 后未置空再引用 | UVS-RES-USE-AFTER-RELEASE（res-use-after-release.md） | 是 | 内部推导 | v0.2 |
| SINK-NULL-DEREF | 空指针解引用 | ONT-SINK | 跨类 | CWE-476 | Py: None 属性访问 · J: null 解引用 · N: null 属性 · PHP: null 调用 · Go: nil 解引用 | UVS-MEM-UNTRUSTED-POINTER（mem-untrusted-pointer.md，相关） | 否 | 内部推导 | v0.2 |
| SINK-INT-OVERFLOW | 整数溢出 | ONT-SINK | 跨类 | CWE-190 | Py: 少见(大整数) · J: int 溢出 · N: Number 精度 · PHP: int 溢出 · Go: int 溢出 · C: malloc(len*sizeof) | UVS-CALC-FAILURE（calc-integer-overflow.md） | 是 | 内部推导 | v0.2 |

## 跨类：资源消耗（DoS）

| stable_id | name | ontology_ref | owasp | cwe | recognition_signals | related_semantics | discoverable | source_refs | version | grep_patterns |
|---|---|---|---|---|---|---|---|---|---|---|
| SINK-RES-CPU | CPU资源消耗(ReDoS) | ONT-RESOURCE-CONSUMPTION | 跨类 | CWE-400/1333 | Py: re.match 嵌套量词 · J: Pattern.compile 嵌套 · N: 嵌套量词 RegExp · PHP: preg_match 嵌套 · Go: regexp 嵌套 | UVS-RES-INEFFICIENT-COMPLEXITY（res-inefficient-complexity.md） | 是 | 内部推导 | v0.2 |
| SINK-RES-MEMORY | 内存资源消耗 | ONT-RESOURCE-CONSUMPTION | 跨类 | CWE-400/789 | Py: 大对象全读入内存 · J: byte[] 大分配 · N: Buffer 无上限 · PHP: memory_limit · Go: 大 make | UVS-RES-UNCONTROLLED-CONSUMPTION（res-uncontrolled-consumption.md） | 是 | 内部推导 | v0.2 |
| SINK-RES-STORAGE | 存储资源消耗 | ONT-RESOURCE-CONSUMPTION | 跨类 | CWE-400/770 | Py: 日志/临时文件无上限 · J: 日志膨胀 · N: 日志膨胀 · PHP: 日志膨胀 · Go: 日志膨胀 | UVS-RES-UNCONTROLLED-CONSUMPTION（res-uncontrolled-consumption.md） | 是 | 内部推导 | v0.2 |
| SINK-RES-CONNECTION | 连接资源消耗 | ONT-RESOURCE-CONSUMPTION | 跨类 | CWE-400/410 | Py: 连接池耗尽 · J: 连接池耗尽 · N: 连接无释放 · PHP: 连接无释放 · Go: 连接无释放 | UVS-RES-IMPROPER-RELEASE（res-improper-release.md） | 是 | 内部推导 | v0.2 |
| SINK-RES-RECURSION | 递归失控 | ONT-RESOURCE-CONSUMPTION | 跨类 | CWE-674 | Py: 递归无 depth 限制 · J: 递归 · N: 递归 · PHP: 递归 · Go: 递归 | UVS-RES-UNCONTROLLED-RECURSION（res-uncontrolled-recursion.md） | 是 | 内部推导 | v0.2 |
| SINK-RES-RATE | 交互频率无限制 | ONT-RESOURCE-CONSUMPTION | 跨类 | CWE-799/770 | Py: 敏感端点无 rate-limit · J: 无 rate-limit · N: 无 rate-limit · PHP: 无 rate-limit · Go: 无 rate-limit | UVS-RES-INTERACTION-FREQUENCY-UNCONTROLLED（res-interaction-frequency.md） | 是 | 内部推导 | v0.2 |

## 其他：状态/并发/文件（补充类）

| stable_id | name | ontology_ref | owasp | cwe | recognition_signals | related_semantics | discoverable | source_refs | version | grep_patterns |
|---|---|---|---|---|---|---|---|---|---|---|
| SINK-STATE-PERM-CHANGE | 权限状态变更 | ONT-STATE-TRANSITION | A01 | CWE-863 | Py: user.role = · J: user.setRole · N: user.role = · PHP: $user->role = · Go: user.Role = | UVS-AC-AUTHORIZATION-FAILURE（相关） | 否 | 内部推导 | v0.1 |
| SINK-STATE-SESSION | 会话状态变更 | ONT-STATE-TRANSITION | A07 | CWE-384 | Py: session.login() / logout() · J: session.invalidate · N: session.destroy · PHP: session_destroy · Go: session.Destroy | UVS-AC-USER-MANAGEMENT-ERROR（相关） | 否 | 内部推导 | v0.1 |
| SINK-STATE-CONCURRENT | 并发竞态(TOCTOU) | ONT-STATE-TRANSITION | 跨类 | CWE-367 | Py: check-then-act 无锁 · J: check-then-act 无同步 · N: 异步竞态 · PHP: 文件竞态 · Go: check-then-act 无锁 | UVS-CONC-RACE-CONDITION（conc-race-condition-toctou.md） | 是 | 内部推导 | v0.2 |
| SINK-FILE-WRITE | 文件写入 | ONT-SINK | A01 | CWE-22/73 | Py: open(...,w) + 用户路径 · J: FileOutputStream + 用户路径 · N: fs.writeFile + 用户路径 · PHP: file_put_contents + 用户路径 · Go: os.WriteFile + 用户路径 | UVS-FILE-PATH-TRAVERSAL（file-path-traversal.md，相关） | 是 | 内部推导 | v0.1 |
| SINK-TEMPLATE-RENDER | 模板渲染 | ONT-SINK | A03 | CWE-79/1336 | Py: render_template( / render_template_string( · J: Thymeleaf / Velocity · N: res.render( / ejs · PHP: twig->render · Go: tmpl.Execute | UVS-INJ-XSS / （SSTI 无专用条目） | 部分 | 内部推导 | v0.1 |
| SINK-LDAP-XPATH | LDAP/XPath查询 | ONT-SINK | A03 | CWE-90/643 | Py: ldap.search / XPath · J: DirContext / XPath · N: ldapjs · PHP: ldap_search / DOMXPath · Go: ldap.Search | （无专用 vuln-pattern） | 否 | 内部推导 | v0.1 |

## 统计与消费方

- 本表 sink 类共 **约 50 类**（A01–A10 × CWE Top 25 2024 双轨 + 跨类内存安全/资源消耗/并发/文件补充类）。
- discoverable=是 的类均有对应 vuln-patterns/ 条目；discoverable=否 或 部分 的类只有识别信号、无完整可执行发现条目，预筛命中后需人工/Agent 逐例判断，不得声称可自动发现。

## 消费方

- candidate-discovery：候选发现能力在传播路径终点识别 Sink/State Transition/Resource Consumption 节点，本表作为预筛 grep 信号目录（命中≠发现，需对应 vuln-patterns 条目支撑）
- verification-and-rating：验证与定级能力评估 Sink 可利用性、State Transition 不变量违反、Resource Consumption 拒绝服务风险
- exploit-proof：利用证明能力针对 Sink/State Transition/Resource Consumption 构造可利用性证明

---

## 缺失检查 sink 类（v0.4 新增，通用负数模式，与任何 CVE 无关）

一类「漏洞=少了一个检查」的缺陷没有危险 API 可 grep（例：不可信值驱动了没有上限保护的循环/分配/强转）。识别用**两段式**：

1. **来源段**（不可信长度/计数/范围值）：请求头数值、帧 payload 长度、content-length、stream id、协议计数字段、数组长度字段；
2. **使用点段**（危险去向）：循环上界 `for(i=0;i<x;i++)`、数组索引 `a[x]`、分配大小 `alloc(x)`、数值强转 `(int)x`。

同一函数/邻近作用域内来源段与使用点段都命中 → 生成检查点（sink_type=SINK-MISSING-CHECK，direction 同普通 sink）。检查点固定问题：**「这个不可信值到达使用点之前，有没有边界检查？」**——有 → 证据行挡住；没有 → 候选（证据=来源行+使用行）。

对抗表模板（每簇必答）：攻击模式=超限循环/负长度/整数溢出截断；目标防御点=边界校验；对抗结果=击破|挡住+证据行。
