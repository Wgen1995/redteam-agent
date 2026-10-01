# 漏洞识别模式知识库索引维护规范（vuln-patterns/）

`index_version: 2.1.0`
`declared_count: 148`
`count_source: index_rows`

> 来源：决策文档 `docs/research/decision/16-gensource-container-design-spec.md`（#16容器设计，已确认）第4节确定的存储形态；`docs/research/decision/24-category15-knowledge-organization-spec.md`（#15知识组织与检索，已确认）第4节索引结构/知识条目内部结构/强制显式查阅纪律；`docs/research/decision/31-category13-language-stack-adaptation-spec.md`（#13语言/技术栈适配，已确认）第5节"适用语言/框架"字段要求；`docs/research/decision/25-category12-scale-cost-management-spec.md`（#12规模成本管理，已确认）第4节"#15知识库索引规模过大时"的应对方案；`docs/research/decision/06-category-scoring-and-recommendations.md`（早期跨竞品打分框架，内容层面仍有效）F1/F2结论。本文件是上述决策规格落地到`knowledge/vuln-patterns/`目录后的**索引维护规范**。

本索引当前登记148条。计数以本文件唯一`VULN-*`数据行为准；每次新增、删除或改名必须同步递增`index_version`并重算计数，不保留会误导消费方的历史“当前条数”声明。

## 1. 这个目录解决什么问题（用途与消费方）

`vuln-patterns/`收录**漏洞识别模式知识**：什么代码信号意味着可能存在某一类漏洞（如"用户输入未经参数化直接拼接进SQL语句"对应SQL注入模式、"反序列化前未校验来源/类型"对应不安全反序列化模式）。这是纯技术性的、有客观信号可循的模式知识——不是业务逻辑判断，也不是攻击手法或修复方案。

**消费方**：`skills/candidate-discovery/SKILL.md`（#3候选发现）的"模式驱动发现"机制（机制一）。该机制对#2攻击面地图上的每一个入口点/危险操作点，比对本目录里的技术性签名，命中即产出候选，并将命中的具体条目ID记录进候选的`discovery_reasoning_note`字段。

**不服务的场景**：#3的"业务逻辑发现"（机制二，推断预期行为再查偏离）与"横向差异发现"（机制三，组内比较离群项）不依赖固定模式，不查本目录。本目录不收录攻击利用手法（那是`attack-patterns/`）或修复方案（那是`fix-patterns/`）。

## 2. 索引表格格式规范

索引是"扫一眼就知道该不该细看"的轻量表格（复用#15已确认原则），不是按字母顺序随便列的清单。列定义：

| 列名 | 含义 |
|---|---|
| 条目ID | 唯一标识，指向`vuln-patterns/`下对应的条目文件（文件命名规则见第3节） |
| 触发信号 | 什么代码信号出现时该查这条——具体到"输入源特征/危险函数调用/框架标记"级别，不是模糊的漏洞类型名称 |
| 适用语言/框架 | 本条目适用的语言/框架范围（#13已确认要求新增此列）。支持先按#1/#2产出的"检测到的语言/框架"事实过滤，不用扫全部条目 |
| 一句话摘要 | 一句话说明这条模式描述的是什么，供扫描判断是否需要打开条目文件细看 |
| 关联UVS | 本条目对应的统一漏洞语义（UVS-\*）引用——KBATCH-001后新增，连接industry-catalog/semantics/ |
| 交叉引用 | 关联的对应`fix-patterns/`条目ID——本模式的标准修复方案，供#7直接查用，不必重新匹配（#15已确认的交叉引用要求） |
| 攻击模式引用 | 关联的`attack-patterns/`条目ID——KBATCH-001后新增，供#6可利用性证明直接查用 |

**当前索引表（148条）**。分层读取顺序固定为：先读本索引并按语言/框架、UVS和触发信号过滤，再只打开命中条目；实际索引与条目read-set写入`knowledge-session-template.md`实例。只有本表存在且链接到真实文件的ID才可写入`vuln_pattern_refs`；查询错误ID或悬空链接时记录`index_coverage_conflict`，不得生成候选或知识引用。

| 条目ID | 触发信号 | 适用语言/框架 | 一句话摘要 | 关联UVS | 交叉引用（fix-pattern条目ID） | 攻击模式引用 |
|---|---|---|---|---|---|---|
| VULN-SQLI-STRCONCAT-01（`sql-injection-string-concat.md`） | `.execute()`第一个参数由`%`/f-string/`+`拼接生成且含可控值；同代码库其他DAO方法用参数化占位符形成横向差异 | 所有直接拼字符串构造SQL的语言（Python/PHP/Java/Node等），验证案例Python+aiopg | SQL语句用字符串拼接/格式化构造后直接execute，而非使用参数化占位符 | UVS-INJ-QUERY-INJECTION | FIX-SQLI-PARAMQUERY-01 | ATK-SQLI-BENIGN-01 |
| VULN-XSS-AUTOESCAPE-01（`template-autoescape-disabled-xss.md`） | 模板引擎setup/配置代码中`autoescape=False`；且存在自由文本字段入库后原样渲染进模板的可达路径 | Jinja2/Django Templates等有全局autoescape开关的模板引擎，验证案例Jinja2(aiohttp_jinja2) | 模板引擎全局关闭自动转义，导致未转义的可控数据渲染进HTML形成XSS | UVS-INJ-XSS | FIX-XSS-AUTOESCAPE-01 | ATK-XSS-BENIGN-DOM-01 |
| VULN-CRYPTO-WEAKHASH-01（`weak-unsalted-password-hash.md`） | 密码字段哈希/比较逻辑使用`hashlib.md5`/`sha1`等通用摘要函数而非bcrypt/argon2/pbkdf2/scrypt；且无per-user随机盐 | 不限语言，密码存储逻辑处均适用，验证案例Python hashlib.md5 | 密码用弱哈希算法且不加盐直接存储/比较，易被彩虹表/暴力破解，且无盐可致跨用户统计分析 | UVS-CRYPTO-WEAK-ALGORITHM | FIX-CRYPTO-STRONGHASH-01 | ATK-CRYPTO-OFFLINE-COST-01 |
| VULN-AUTHZ-MISSING-01（`missing-authorization-check.md`） | 同一路由文件内，状态变更类端点(POST/PUT/DELETE)部分有授权装饰器/中间件调用、部分没有，形成同组离群项 | 所有有装饰器/中间件式授权机制的Web框架，验证案例Python aiohttp自定义装饰器 | 状态变更类端点缺少授权检查，而同代码库其他类似端点有，可由横向差异发现机制定位 | UVS-AC-AUTHORIZATION-FAILURE | FIX-AUTHZ-ADDCHECK-01 | ATK-AUTHZ-DUAL-IDENTITY-01 |
| VULN-AC-USERMGMT-01（`session-fixation-user-confusion.md`） | 认证成功后设置会话身份，但未调用session regeneration/cycle_key/changeSessionId | Python/Java/PHP/Node.js/Go等有状态会话框架 | 会话固定或身份混淆使攻击者预设会话在受害者登录后仍有效 | UVS-AC-USER-MANAGEMENT-ERROR | FIX-AC-SESSION-REGEN-01 | ATK-AUTHN-SESSION-FIXATION-01 |
| VULN-HYGIENE-DEADCONTROL-01（`dead-security-control.md`） **[低置信度/待观察，见条目内声明]** | 中间件注册列表中被注释掉的行；定义了但全代码库无引用的校验schema；实现了分支逻辑但从未被以该分支条件调用的函数参数 | 不限语言/框架，任何需显式装配才生效的安全机制架构均适用，验证案例Python aiohttp | 安全防护机制已实现但从未被实际装配/引用，造成虚假安全感（本条目仅1次独立观察，未达#16跨≥2场景晋升门槛） | UVS-PROT-ADMIN-CONTROL-FAILURE | FIX-DEADCONTROL-ASSEMBLY-01 | 不适用（无独立活攻击面） |
| VULN-XSS-RAWOUTPUT-01（`raw-output-no-escaping-xss.md`） **[Inferred级别，见条目内声明]** | `echo`/`print`/拼接返回值等原生输出语句，参数含可控值且未经转义函数包裹，且路径上不存在模板引擎介入 | 原生PHP/原生JSP/任何不经过带自动转义能力模板层的场景；与VULN-XSS-AUTOESCAPE-01互斥判断（先确认是否存在模板引擎） | 无模板引擎默认转义机制介入的原生输出XSS，跟"默认防护被关闭"是不同成因，2026-08-08跨语言泛化测试发现的知识空白补齐 | UVS-INJ-XSS | FIX-XSS-OUTPUT-ENCODING-01 | ATK-XSS-BENIGN-DOM-01 |
| VULN-INJ-NEUTRALIZE-01（`inj-neutralization-failure.md`） **[Inferred，抽象根模式]** | 跨信任边界数据到达解释器前未中和；无法匹配更具体子模式时的fallback语义框架 | 不限语言/框架（抽象根模式） | 数据到达解释器前未中和——注入域根模式，仅在无法匹配具体子模式时作为fallback使用 | UVS-INJ-NEUTRALIZATION-FAILURE | 不适用（抽象根模式） | 不适用（抽象根模式） |
| VULN-INJ-SPECELEM-01（`inj-special-element-failure.md`） **[Inferred]** | 日志写入/CSV导出/EL求值/模板渲染调用的参数含可控值且特殊元素未移除；不归入更具体子模式 | 不限语言/框架，日志/CSV/EL/模板引擎场景 | 分隔符/元字符/控制字符未中和——覆盖不归入更具体子模式的通用特殊元素处理场景 | UVS-INJ-SPECIAL-ELEMENT-FAILURE | FIX-INJ-SPECELEM-01 | ATK-INJ-SPECELEM-01 |
| VULN-INJ-CMD-01（`inj-command-injection.md`） | `os.system`/`subprocess(shell=True)`/`exec`等命令执行调用的参数由拼接生成且含可控值 | Python/PHP/Java/Node.js/Go/Ruby等所有执行shell命令的语言，验证案例Python | shell命令用字符串拼接把可控值嵌入命令文本后执行，而非使用参数数组形式 | UVS-INJ-COMMAND-INJECTION | FIX-INJ-CMD-01 | ATK-INJ-CMD-01 |
| VULN-INJ-RESOURCE-01（`inj-resource-injection.md`） | `open`/`include`/`requests.get`等资源访问调用的路径/URL参数含可控值且未经白名单/规范化/前缀绑定 | Python/PHP/Java/Node.js/Go等所有将外部输入用作资源标识符的语言，验证案例Python | 外部输入直接用作文件路径/URL/连接目标等资源标识符，未经白名单/规范化/前缀绑定验证 | UVS-INJ-RESOURCE-INJECTION | FIX-INJ-RESOURCE-01 | ATK-INJ-RESOURCE-01 |
| VULN-INJ-CRLF-01（`inj-crlf-injection.md`） **[Inferred]** | HTTP响应头设置/日志写入/邮件头构造的参数含可控值且CRLF字符未移除；目标框架未内置CRLF过滤 | Python/Java/PHP/Node.js等所有构造行结构数据的语言 | CRLF序列未中和注入HTTP头/日志/邮件头，导致HTTP响应分割/日志伪造/邮件头注入 | UVS-INJ-CRLF | FIX-INJ-CRLF-01 | ATK-INJ-CRLF-01 |
| VULN-INJ-CODE-01（`inj-code-injection.md`） | `eval`/`exec`/`new Function`/`ScriptEngine.eval`等动态代码执行调用的代码参数位含可控值 | Python/PHP/JavaScript/Java/Ruby/Shell等所有支持动态代码执行的语言，验证案例Python | 外部输入直接用于动态代码执行的代码参数位，或被拼入模板字符串本身 | UVS-INJ-CODE-INJECTION | FIX-INJ-CODE-01 | ATK-INJ-CODE-01 |
| VULN-INJ-FMTSTR-01（`inj-format-string.md`） **[Inferred]** | `printf`/`sprintf`/`fprintf`/`syslog`的格式字符串参数位含可控值（而非数据参数位） | C/C++/PHP等使用格式化字符串机制的语言 | 外部输入被用作格式化函数的格式字符串参数位，格式化说明符被解释为控制语义 | UVS-INJ-FORMAT-STRING | FIX-INJ-FMTSTR-01 | ATK-INJ-FMTSTR-01 |
| VULN-INJ-XXE-01（`inj-xxe.md`） **[Inferred]** | XML解析器接受不可信输入且未禁用外部实体/DTD/外部参数实体处理 | Java/Python(lxml)/PHP/.NET等所有解析XML的语言，验证案例Java+Python | XML解析器未禁用外部实体处理，导致通过恶意XML读取本地文件/发起网络请求 | UVS-INJ-XXE | FIX-INJ-XXE-01 | ATK-INJ-XXE-01 |
| VULN-INJ-SSRF-01（`inj-ssrf.md`） | `requests.get`/`http.get`/`HttpClient`等服务端网络请求调用的URL参数含可控值且未经白名单/内部地址段/协议验证 | Python/Java/Node.js/PHP/Go等所有支持HTTP客户端库的语言，验证案例Python | 服务端使用用户可控URL发起网络请求且未验证目标，可访问内部服务/云元数据端点 | UVS-INJ-SSRF | FIX-INJ-SSRF-01 | ATK-INJ-SSRF-01 |
| VULN-INJ-DESERIAL-01（`inj-deserialization.md`） | `pickle.loads`/`ObjectInputStream.readObject`/`unserialize`/`BinaryFormatter.Deserialize`等原生反序列化调用接受不可信数据且无类型白名单 | Python/Java/PHP/.NET/Ruby/Node.js等所有支持原生对象序列化的语言，验证案例Python | 不受信任来源的序列化数据被直接反序列化，未限制可反序列化的对象类型 | UVS-INJ-DESERIALIZATION | FIX-INJ-DESERIAL-01 | ATK-INJ-DESERIAL-01 |
| VULN-HW-MEMPROT-01（`hw-memory-protection-missing.md`） **[Proposed]** | MMU/MPU页表配置W和X位同时设置；受保护范围与普通范围重叠；镜像区域无一致性校验 | C/嵌入式固件/MMU/MPU/SoC fabric防火墙 | 硬件内存保护机制（W^X/范围隔离/镜像一致性/分配控制）未正确配置或执行 | UVS-HW-MEMORY-PROTECTION-FAILURE | FIX-HW-MEMPROT-01 | ATK-HW-MEMPROT-01 |
| VULN-HW-DEBUG-01（`hw-debug-interface-exposed.md`） **[Proposed]** | JTAG/SWD接口生产环境未熔断；测试逻辑可运行时激活；备用接口可访问 | IoT/嵌入式设备/SoC安全 | 硬件调试/测试/备用接口生产环境中仍可被激活或访问 | UVS-HW-DEBUG-INTERFACE-FAILURE | FIX-HW-DEBUG-01 | ATK-HW-DEBUG-01 |
| VULN-HW-FIRMWARE-01（`hw-firmware-update-missing.md`） **[Proposed]** | 固件存储在ROM不可更新；无OTA更新接口；ROM无补丁机制 | IoT/嵌入式设备/SoC安全 | 固件或ROM代码无法被安全更新或修补，已知漏洞无法修复 | UVS-HW-FIRMWARE-UPDATE-FAILURE | FIX-HW-FIRMWARE-01 | ATK-HW-FIRMWARE-01 |
| VULN-HW-ROOT-01（`hw-root-of-trust-writable.md`） **[Proposed]** | 信任根存储在可写内存而非ROM/eFuse；假定不可变数据实际可被修改 | C/嵌入式固件/eFuse/ROM/TPM | 硬件信任根缺失或可被篡改，安全启动/远程证明可信基础被破坏 | UVS-HW-ROOT-OF-TRUST-FAILURE | FIX-HW-ROOT-01 | ATK-HW-ROOT-01 |
| VULN-HW-LOGIC-01（`hw-logic-fault-fsm-missing.md`） **[Proposed]** | FSM case语句无default/error状态；控制与数据通道无同步检测；指令跳过无故障检测 | Verilog/VHDL/SoC设计/硬件安全 | 硬件逻辑FSM/去同步化/指令跳过故障处理缺失 | UVS-HW-LOGIC-FAULT-FAILURE | FIX-HW-LOGIC-01 | ATK-HW-LOGIC-01 |
| VULN-HW-FABRIC-01（`hw-fabric-security-missing.md`） **[Proposed]** | 总线无AxPROT安全位；参数数据无写保护；fabric端点无访问控制 | Verilog/VHDL/SoC/AXI/AHB | 片上总线/互联安全特性缺失或写保护配置不当 | UVS-HW-FABRIC-SECURITY-FAILURE | FIX-HW-FABRIC-01 | ATK-HW-FABRIC-01 |
| VULN-HW-RE-01（`hw-reverse-engineering-unprotected.md`） **[Proposed]** | 芯片无金属层遮挡；敏感走线无屏蔽；无防拆解机制；无探测传感器 | IC设计/SoC安全/嵌入式安全 | 硬件缺乏逆向工程和物理探测防护，设计信息或密钥可被提取 | UVS-HW-REVERSE-ENGINEERING-FAILURE | FIX-HW-RE-01 | ATK-HW-RE-01 |
| VULN-CODE-DANGEROUS-01（`code-dangerous-function-usage.md`） **[Proposed]** | gets/strcpy/sprintf/scanf等危险函数调用且输入来自外部 | C/C++/Java(JNI)/通用linter | 使用已知不安全的危险函数（无边界检查），应使用安全替代 | UVS-CODE-DANGEROUS-FUNCTION | FIX-CODE-DANGEROUS-01 | ATK-CODE-DANGEROUS-01 |
| VULN-CODE-DYNCTRL-01（`code-dynamic-control-missing.md`） **[Proposed]** | __import__/importlib/ClassLoader动态加载目标标识来自外部且无白名单 | Python/Java/Node.js/通用插件系统 | 动态代码资源控制缺失——动态加载未验证来源或完整性 | UVS-CODE-DYNAMIC-CONTROL-FAILURE | FIX-CODE-DYNCTRL-01 | ATK-CODE-DYNCTRL-01 |
| VULN-CODE-EMBEDDED-01（`code-embedded-malicious.md`） **[Proposed]** | 第三方包来源不可信；安装脚本有可疑操作；构建不可重现 | npm/PyPI/通用供应链 | 嵌入式恶意代码——第三方包/构建产物中包含特洛伊木马/活板门/逻辑炸弹 | UVS-CODE-EMBEDDED-MALICIOUS | FIX-CODE-EMBEDDED-01 | ATK-CODE-EMBEDDED-01 |
| VULN-CODE-HIDDEN-01（`code-hidden-functionality.md`） **[Proposed]** | debug_mode参数触发特权操作；未文档化路由/端点；活动调试代码 | Web/桌面/移动/通用feature flag | 隐藏功能/活动调试代码——未文档化功能或调试端点生产环境可用 | UVS-CODE-HIDDEN-FUNCTIONALITY | FIX-CODE-HIDDEN-01 | ATK-CODE-HIDDEN-01 |
| VULN-CODE-PROHIBITED-01（`code-prohibited-usage.md`） **[Proposed]** | 使用禁用API列表中的函数且无linter/CI门控检测 | C/C++/Java/通用linter/CI | 使用禁用代码——被明确禁止的API/函数未被检测或阻止 | UVS-CODE-PROHIBITED-USAGE | FIX-CODE-PROHIBITED-01 | ATK-CODE-PROHIBITED-01 |
| VULN-CODE-SPECMISMATCH-01（`code-specification-mismatch.md`） **[Proposed]** | 实现的安全检查与规范定义不一致（简化/遗漏/改变） | 不限语言/框架（有规范文档的项目） | 功能实现与规范不匹配——安全行为偏离预期 | UVS-CODE-SPECIFICATION-MISMATCH | FIX-CODE-SPECMISMATCH-01 | ATK-CODE-SPECMISMATCH-01 |
| VULN-CODE-UNDEF-01（`code-undefined-behavior.md`） **[Proposed]** | 有符号整数溢出；未初始化变量；memset清零可被优化掉 | C/C++/Rust(unsafe)/通用编译器 | 依赖未定义行为——不同平台/编译器/优化级别产生不同结果 | UVS-CODE-UNDEFINED-BEHAVIOR | FIX-CODE-UNDEF-01 | ATK-CODE-UNDEF-01 |
| VULN-AI-PROMPTINJ-01（`ai-prompt-injection.md`） **[Proposed]** | 用户输入直接拼接到系统提示（字符串拼接而非结构化消息） | LLM应用(OpenAI/Anthropic/LangChain) | LLM提示注入——用户输入与系统指令未隔离，可覆盖系统指令 | UVS-AI-PROMPT-INJECTION | FIX-AI-PROMPTINJ-01 | ATK-AI-PROMPTINJ-01 |
| VULN-AI-ADVERSARIAL-01（`ai-adversarial-input.md`） **[Proposed]** | AI/ML推理无对抗性检测；无输出置信度校验；模型未对抗性训练 | ML框架(TensorFlow/PyTorch)/识别系统 | 对抗性输入处理不足——模型对扰动输入产生错误输出 | UVS-AI-ADVERSARIAL-INPUT | FIX-AI-ADVERSARIAL-01 | ATK-AI-ADVERSARIAL-01 |
| VULN-AI-CONFIG-01（`ai-insecure-inference-config.md`） **[Proposed]** | 推理参数temperature>1.0/top_p=1.0；参数可被外部控制 | LLM应用(OpenAI/Anthropic API)/ML运维 | AI模型推理参数不安全配置——温度过高/top_p不限制导致输出不受约束 | UVS-AI-INSECURE-CONFIGURATION | FIX-AI-CONFIG-01 | ATK-AI-CONFIG-01 |
| VULN-AI-OUTPUT-01（`ai-output-validation-missing.md`） **[Proposed]** | AI生成代码exec()执行；AI输出直接存储/展示无校验 | LLM应用/代码生成/通用AI输出消费 | 生成式AI输出验证失效——AI输出未经校验即进入下游系统 | UVS-AI-OUTPUT-VALIDATION-FAILURE | FIX-AI-OUTPUT-01 | ATK-AI-OUTPUT-01 |
| VULN-AI-OPTIMIZATION-01（`ai-insecure-optimization.md`） **[Proposed]** | 安全代码memset清零无volatile保护；无优化前后安全行为验证 | C/C++编译器/AI模型优化/自动调优 | 不安全自动化优化——优化移除或改变安全关键代码 | UVS-AI-INSECURE-OPTIMIZATION | FIX-AI-OPTIMIZATION-01 | ATK-AI-OPTIMIZATION-01 |
| VULN-SPHERE-ISOLATION-01（`sphere-isolation-failure.md`） **[Proposed]** | 多租户查询未过滤tenant_id；容器无namespace/cgroup；进程间共享内存未隔离 | SaaS/容器/Unix/Electron | 隔离失效——不同主体/租户/进程之间未有效隔离 | UVS-SPHERE-ISOLATION-FAILURE | FIX-SPHERE-ISOLATION-01 | ATK-SPHERE-ISOLATION-01 |
| VULN-SPHERE-ALTPATH-01（`sphere-alternate-path-unprotected.md`） **[Proposed]** | 主API有认证但调试API/直接访问/管理端口无认证 | Web/微服务/通用多路径系统 | 替代路径保护不当——主路径有安全控制但替代路径没有 | UVS-SPHERE-ALTERNATE-PATH-UNPROTECTED | FIX-SPHERE-ALTPATH-01 | ATK-SPHERE-ALTPATH-01 |
| VULN-SPHERE-CHANNEL-01（`sphere-channel-accessible.md`） **[Proposed]** | 网络通信使用明文HTTP；未加密socket；无证书验证 | 不限语言/HTTP/socket/消息队列 | 通信信道可被非端点访问——信道未加密/未认证/可被中间人介入 | UVS-SPHERE-CHANNEL-ACCESSIBLE-BY-NON-ENDPOINT | FIX-SPHERE-CHANNEL-01 | ATK-SPHERE-CHANNEL-01 |
| VULN-SPHERE-EXTINFLUENCE-01（`sphere-external-influence.md`） **[Proposed]** | 信任域配置接口无权限控制；外部输入可修改域定义 | K8s/云服务/Web配置 | 域定义外部影响——外部主体能影响信任域定义或边界划分 | UVS-SPHERE-EXTERNAL-INFLUENCE | FIX-SPHERE-EXTINFLUENCE-01 | ATK-SPHERE-EXTINFLUENCE-01 |
| VULN-SPHERE-EXTREF-01（`sphere-external-reference.md`） **[Proposed]** | URL/引用参数来自外部且无白名单/内网过滤 | Web/API/OAuth/服务间通信 | 外部控制跨域引用——外部输入直接用作跨域资源引用未验证 | UVS-SPHERE-EXTERNAL-REFERENCE | FIX-SPHERE-EXTREF-01 | ATK-SPHERE-EXTREF-01 |
| VULN-SPHERE-TRANSFER-01（`sphere-incorrect-transfer.md`） **[Proposed]** | API响应包含内部数据字段；跨域消息传递无数据过滤 | 微服务/API Gateway/通用跨域传输 | 域间资源错误转移——跨域转移未验证目标域或无数据过滤 | UVS-SPHERE-INCORRECT-TRANSFER | FIX-SPHERE-TRANSFER-01 | ATK-SPHERE-TRANSFER-01 |
| VULN-SPHERE-EXPOSURE-01（`sphere-wrong-exposure.md`） **[Proposed]** | 管理接口绑定0.0.0.0；文件权限过宽；无NetworkPolicy/安全组 | Web/K8s/云服务/通用服务暴露 | 资源暴露到错误域——管理接口公网暴露/文件权限过宽 | UVS-SPHERE-WRONG-EXPOSURE | FIX-SPHERE-EXPOSURE-01 | ATK-SPHERE-EXPOSURE-01 |
| VULN-UI-MISREP-01（`ui-misrepresentation.md`） **[Proposed]** | 链接显示文本与href不一致；同形字未检测；发件人地址伪造 | 浏览器/邮件/Web/移动 | 关键信息UI误表示——显示的关键信息与实际不一致 | UVS-UI-MISREPRESENTATION | FIX-UI-MISREP-01 | ATK-UI-MISREP-01 |
| VULN-UI-WARNING-01（`ui-insufficient-warning.md`） **[Proposed]** | 危险操作无确认对话框；安全设置变更无警告；无二次确认 | Web/桌面/移动 | UI安全警告不足——危险操作缺乏警告提示 | UVS-UI-INSUFFICIENT-WARNING | FIX-UI-WARNING-01 | ATK-UI-WARNING-01 |
| VULN-UI-DISCREPANCY-01（`ui-security-discrepancy.md`） **[Proposed]** | UI显示HTTPS但表单提交到HTTP；安全开关显示与实际不一致 | Web/移动/桌面 | 安全功能UI差异——安全状态显示与实际行为不一致 | UVS-UI-SECURITY-DISCREPANCY | FIX-UI-DISCREPANCY-01 | ATK-UI-DISCREPANCY-01 |
| VULN-INTER-CONFUSED-01（`inter-confused-deputy.md`） **[Proposed]** | 有权限代理程序未验证请求方权限；编译器/API Gateway执行特权操作 | 编译器/API Gateway/系统服务/特权服务 | 混淆代理人——有权限代理被低权限主体误导执行特权操作 | UVS-INTER-CONFUSED-DEPUTY | FIX-INTER-CONFUSED-01 | ATK-INTER-CONFUSED-01 |
| VULN-INTER-INTERPCONFLICT-01（`inter-interpretation-conflict.md`） **[Proposed]** | 跨组件URL规范化差异；编码规范化差异；HTTP请求解析差异 | URL解析/编码/HTTP请求解析/协议交互 | 解释冲突——两个实体对同一数据有不同解释 | UVS-INTER-INTERPRETATION-CONFLICT | FIX-INTER-INTERPCONFLICT-01 | ATK-INTER-INTERPCONFLICT-01 |
| VULN-INTER-SPECVIOLATION-01（`inter-spec-violation-by-caller.md`） **[Proposed]** | 调用方未初始化结构体就传递；参数约束违反；调用顺序错误 | C/Rust/通用API/库接口 | 调用方违反规范——未按被调用方规范使用接口 | UVS-INTER-SPEC-VIOLATION-BY-CALLER | FIX-INTER-SPECVIOLATION-01 | ATK-INTER-SPECVIOLATION-01 |
| VULN-SUPPLY-UNTRUSTWORTHY-01（`supply-untrustworthy-component.md`） **[Proposed]** | 第三方包非verified publisher；无provenance；无签名检查 | npm/PyPI/通用包管理 | 不可信组件依赖——使用了未经验证或信任度不足的第三方组件 | UVS-SUPPLY-UNTRUSTWORTHY-COMPONENT | FIX-SUPPLY-UNTRUSTWORTHY-01 | ATK-SUPPLY-UNTRUSTWORTHY-01 |
| VULN-SUPPLY-VULNDEP-01（`supply-vulnerable-dependency.md`） **[Proposed]** | 依赖版本包含已知CVE；无SCA扫描；无自动更新 | npm/PyPI/通用SCA/Dependabot | 依赖易受攻击第三方组件——使用了包含已知漏洞的组件 | UVS-SUPPLY-VULNERABLE-DEPENDENCY | FIX-SUPPLY-VULNDEP-01 | ATK-SUPPLY-VULNDEP-01 |
| VULN-STATE-EXTCONTROL-01（`state-external-control.md`） **[Proposed]** | 外部输入直接控制role/is_admin/permissions字段；mass assignment | Web(mass assignment)/API/PHP | 关键状态数据外部控制——外部输入直接控制关键状态 | UVS-STATE-EXTERNAL-CONTROL | FIX-STATE-EXTCONTROL-01 | ATK-STATE-EXTCONTROL-01 |
| VULN-STATE-INCOMPLETE-01（`state-incomplete-distinction.md`） **[Proposed]** | 部分认证被当作完全认证处理；未区分初始/已配置状态 | 状态机/认证框架/通用状态管理 | 内部状态区分不完整——安全相关状态未被正确区分 | UVS-STATE-INCOMPLETE-DISTINCTION | FIX-STATE-INCOMPLETE-01 | ATK-STATE-INCOMPLETE-01 |
| VULN-PHYSICAL-ENV-01（`physical-environment-failure.md`） **[Proposed]** | 无电压/温度监测代码；无故障注入防护；环境异常时未进入安全状态 | 硬件安全/IoT/嵌入式 | 物理/环境条件处理不当——未检测或处理环境异常 | UVS-PHYSICAL-ENVIRONMENT-FAILURE | FIX-PHYSICAL-ENV-01 | ATK-PHYSICAL-ENV-01 |
| VULN-PHYSICAL-POWER-01（`physical-power-consumption.md`） **[Proposed]** | 密码操作依赖密钥位条件分支（不同路径功耗不同）；无恒定功耗 | 嵌入式/智能卡/硬件密码 | 功耗限制不当——功耗轨迹泄露秘密信息（侧信道攻击） | UVS-PHYSICAL-POWER-CONSUMPTION | FIX-PHYSICAL-POWER-01 | ATK-PHYSICAL-POWER-01 |
| VULN-TYPE-CAST-01（`type-incorrect-cast.md`） **[Proposed]** | 有符号到无符号转换（-1→UINT_MAX）；窄化转换截断；符号扩展 | C/C++/Rust(unsafe)/Java/通用类型转换 | 类型转换错误——转换产生非预期结果 | UVS-TYPE-INCORRECT-CAST | FIX-TYPE-CAST-01 | ATK-TYPE-CAST-01 |
| VULN-NAME-RESOLUTION-01（`name-incorrect-resolution.md`） **[Proposed]** | sys.path可被修改；DNS可被劫持；引用路径可被控制 | Python(模块搜索)/DNS/通用名称解析 | 名称/引用解析错误——解析被劫持或指向错误目标 | UVS-NAME-INCORRECT-RESOLUTION | FIX-NAME-RESOLUTION-01 | ATK-NAME-RESOLUTION-01 |
| VULN-PROCESS-CONTROL-01（`process-control-failure.md`） **[Proposed]** | 外部输入控制进程执行代码；进程创建未验证；进程权限未限制 | OS/容器/通用进程管理 | 进程控制失效——进程创建/执行未验证或权限未限制 | UVS-PROCESS-CONTROL-FAILURE | FIX-PROCESS-CONTROL-01 | ATK-PROCESS-CONTROL-01 |
| VULN-LOGGING-INSUFFICIENT-01（`logging-insufficient.md`） **[Proposed]** | 安全关键操作（认证/授权/特权）无日志记录；日志内容不足actor/action/target/timestamp | Python(logging)/Java(SLF4J)/通用日志 | 日志记录不足——安全事件未被充分记录 | UVS-LOGGING-INSUFFICIENT | FIX-LOGGING-INSUFFICIENT-01 | 不适用（无独立活攻击面） |
| VULN-ENCAP-INSUFFICIENT-01（`encapsulation-insufficient.md`） **[Proposed]** | 关键数据声明为public；返回可变对象给不可信调用方；传递可变对象给不可信方法 | Java/C++/Python/通用OOP | 封装不足——内部状态或实现细节被不当地暴露 | UVS-ENCAP-INSUFFICIENT | FIX-ENCAP-INSUFFICIENT-01 | ATK-ENCAP-INSUFFICIENT-01 |
| VULN-ENC-ENCODING-01（`encoding-failure.md`） **[Proposed]** | 可控数据输出到HTML/JS/URL未编码；输出编码与上下文不匹配 | Python(Jinja2)/Java(OWASP Encoder)/通用模板 | 输出编码失效——数据输出到上下文未经过正确编码或转义 | UVS-ENC-ENCODING-FAILURE | FIX-ENC-ENCODING-01 | ATK-ENC-ENCODING-01 |
| VULN-CRYPTO-NOENCRYPT-01（`missing-encryption-cleartext.md`） **[Proposed]** | 敏感数据传输走`http://`或禁用TLS校验(`verify=False`/`InsecureSkipVerify`)；敏感字段明文存储/明文入日志 | 不限语言，传输侧(requests/URLConnection/http)与存储侧(ORM/日志/文件)均适用 | 敏感数据传输/存储未加密，明文通道可被截获、明文存储可被直接读取 | UVS-CRYPTO-MISSING-ENCRYPTION | FIX-CRYPTO-ENFORCEENC-01 | ATK-CRYPTO-CLEARTEXT-01 |
| VULN-CRYPTO-WEAKSTRENGTH-01（`weak-crypto-strength-params.md`） **[Proposed]** | 密钥生成参数低于基线(RSA<2048/对称<128/ECC<224)；KDF迭代过低(bcrypt<10/PBKDF2<600000)；IV/nonce过短 | Python(cryptography)/Java(JCA)/Node(crypto)/Go(crypto/rsa)等所有支持加密API的语言 | 加密强度参数不足——有加密但密钥长度/迭代次数/IV长度低于当前安全基线 | UVS-CRYPTO-WEAK-STRENGTH | FIX-CRYPTO-ADEQUATESTRENGTH-01 | ATK-CRYPTO-KEYSIZE-01 |
| VULN-CRYPTO-WEAKRNG-01（`insufficient-randomness-noncsprng.md`） **[Proposed]** | 安全场景(令牌/密钥/IV/nonce/盐)使用`random`/`Math.random`/`java.util.Random`/`math/rand`而非CSPRNG；或可预测种子(时间戳) | Python(random vs secrets)/Java(Random vs SecureRandom)/Node(Math.random vs crypto)/Go(math/rand vs crypto/rand) | 安全场景使用非CSPRNG或可预测种子，随机值可被预测重现 | UVS-CRYPTO-INSUFFICIENT-RANDOMNESS | FIX-CRYPTO-CSPRNG-01 | ATK-CRYPTO-RNGPREDICT-01 |
| VULN-CRYPTO-PREDICTID-01（`predictable-identifier-generation.md`） **[Proposed]** | 安全标识符用顺序自增/时间戳/可推断命名规则生成；且标识符可被外部引用(API路径参数) | 不限语言，数据库自增主键作公开标识/时间戳ID/可推断命名场景 | 安全标识符生成策略可预测——顺序/时间戳/可推断规则，可枚举推算他人标识符 | UVS-CRYPTO-PREDICTABLE-IDENTIFIER | FIX-AUTHN-SECURE-ID-01(复用AUTHN域) | ATK-AUTHN-ID-PREDICT-01(复用AUTHN域) |
| VULN-CRYPTO-NOAUTHVERIFY-01（`missing-authenticity-verification.md`） **[Proposed]** | 接收外部数据(更新包/API响应/依赖)未验证签名/证书/完整性；或TLS校验被禁用(`verify=False`/`InsecureSkipVerify`/`rejectUnauthorized:false`) | Python(requests/urllib)/Java(JCA SSLContext)/Node(https)/Go(crypto/tls)等所有接收外部数据的场景 | 外部数据接收未验证来源真实性，伪造/篡改数据被信任处理 | UVS-CRYPTO-AUTHENTICITY-VERIFICATION-FAILURE | FIX-CRYPTO-VERIFYAUTH-01 | ATK-CRYPTO-FORGEDDATA-01 |
| VULN-CRYPTO-NOORIGIN-01（`missing-origin-validation.md`） **[Proposed]** | 状态变更操作(POST/PUT/DELETE)无CSRF token校验；`@csrf_exempt`/`@csrf.exempt`；Cookie未设SameSite；CORS`*`+Credentials；WebSocket无Origin校验 | Django/Flask/Express/Spring等Web框架及WebSocket场景 | 状态变更请求未验证来源(CSRF/跨域)，未授权来源请求被接受执行 | UVS-AC-AUTHORIZATION-FAILURE | FIX-CRYPTO-ORIGIN-01 | ATK-CRYPTO-CSRF-01 |
| VULN-CRYPTO-KEYLIFE-01（`key-lifecycle-nonce-reuse.md`） **[Proposed]** | 加密nonce/IV固定或重复使用(CTR/GCM下重用即灾难)；密钥硬编码源码(`key=b'...'`)；过期/泄露密钥未撤销；调试生产密钥复用 | Python(cryptography)/Java(JCA)/Node(crypto)/Go(cipher)等所有加密场景 | 密钥/nonce生命周期管理失效——重用/过期未撤销/硬编码，破坏密码学安全保证 | UVS-CRYPTO-KEY-LIFECYCLE-FAILURE | FIX-CRYPTO-KEYLIFE-01 | ATK-CRYPTO-NONCEREUSE-01 |
| VULN-CRYPTO-MISSINGSTEP-01（`missing-crypto-step-mac.md`） **[Proposed]** | 加密用CBC/CTR等非AEAD模式且无伴随MAC/AEAD调用；密钥协商(DH/ECDH)无实体认证；签名验证不完整 | Python(cryptography)/Java(JCA)/Node(crypto)/Go(cipher)等所有加密/签名场景 | 密码学操作步骤缺失——仅加密未认证/密钥协商缺认证，保护可被绕过 | UVS-CRYPTO-MISSING-STEP | FIX-CRYPTO-AEAD-01 | ATK-CRYPTO-TAMPER-01 |
| VULN-MEM-BOUNDS-01（`mem-bounds-failure.md`） **[Inferred]** | `memcpy`/`strcpy`/`strcat`/`sprintf`调用的长度参数来自源或外部输入而非目标缓冲区大小 | C/C++(无边界检查函数)/Rust(unsafe)/Python(ctypes)/Java(Unsafe)/Go(unsafe) | 缓冲区拷贝/读写操作的字节数未与缓冲区实际大小比较，导致越界读写 | UVS-MEM-BOUNDS-FAILURE | FIX-MEM-BOUNDS-01 | ATK-MEM-BOUNDS-01 |
| VULN-MEM-INDEX-01（`mem-index-access-error.md`） **[Inferred]** | 数组下标`arr[index]`/指针算术`ptr+offset`的索引值来自外部输入且未检查范围 | C/C++(裸数组)/Rust(unsafe)/Python(ctypes)/Java(Unsafe)/Go(unsafe) | 数组/缓冲区索引值来自外部输入或计算结果但未检查范围，导致越界访问 | UVS-MEM-INDEX-ACCESS-ERROR | FIX-MEM-INDEX-01 | ATK-MEM-INDEX-01 |
| VULN-MEM-LAYOUT-01（`mem-layout-reliance.md`） **[Inferred]** | `memcpy(&struct, data, sizeof(struct))`整体memcpy网络数据到结构体；`union`类型双关 | C/C++(结构体memcpy/union)/Rust(unsafe transmute) | 依赖实现定义的内存布局（结构体对齐/大小端/位域），直接将外部数据memcpy到结构体 | UVS-MEM-LAYOUT-RELIANCE | FIX-MEM-LAYOUT-01 | ATK-MEM-LAYOUT-01 |
| VULN-MEM-NULLTERM-01（`mem-null-termination.md`） **[Inferred]** | `strncpy`后未设`buf[n-1]='\0'`；`memcpy`字符串后未添加终止符；后续有`strlen`/`strcpy`依赖终止符 | C(strncpy陷阱)/C++(char*操作) | 字符串操作未确保缓冲区末尾存在空终止符，导致后续strlen/strcpy读取超出预期范围 | UVS-MEM-NULL-TERMINATION | FIX-MEM-NULLTERM-01 | ATK-MEM-NULLTERM-01 |
| VULN-MEM-PTR-01（`mem-untrusted-pointer.md`） **[Inferred]** | IOCTL输入结构体中的指针字段被直接解引用；外部整数被强制转换为指针 | C/C++(kernel IOCTL)/Rust(unsafe)/Python(ctypes)/Java(Unsafe)/Go(unsafe) | 外部输入被直接转换为指针并解引用，未验证来源可信性和值域合法性 | UVS-MEM-UNTRUSTED-POINTER | FIX-MEM-PTR-01 | ATK-MEM-PTR-01 |
| VULN-FILE-TRAVERSAL-01（`file-path-traversal.md`） **[Inferred]** | `open`/`fopen`/`include`等文件操作的路径参数含外部输入拼接且未规范化验证 | 所有将外部输入用作文件路径的语言(Python/Java/Node/PHP/Go/C) | 外部输入用于构造文件路径时未中和`../`等遍历序列，导致访问预期目录之外的文件 | UVS-FILE-PATH-TRAVERSAL | FIX-FILE-TRAVERSAL-01 | ATK-FILE-TRAVERSAL-01 |
| VULN-FILE-SYMLINK-01（`file-link-following.md`） **[Inferred]** | `open`/`fopen`默认跟随symlink且文件路径位于攻击者可写目录；未使用`O_NOFOLLOW` | C/Python/Java/Go/Rust等所有支持symlink的OS上的文件操作 | 程序在访问控制检查后跟随符号链接而非先解析链接目标再检查 | UVS-FILE-LINK-FOLLOWING | FIX-FILE-SYMLINK-01 | ATK-FILE-SYMLINK-01 |
| VULN-FILE-PATHEQUIV-01（`file-path-equivalence.md`） **[Inferred]** | 路径黑名单/白名单/前缀匹配使用原始路径而非规范形式；Windows未考虑大小写/末尾点 | 所有在路径上做安全检查的语言/框架 | 路径安全检查基于非规范路径表示，攻击者利用等价路径表示绕过检查 | UVS-FILE-PATH-EQUIVALENCE | FIX-FILE-PATHEQUIV-01 | ATK-FILE-PATHEQUIV-01 |
| VULN-FILE-VIRTUAL-01（`file-virtual-resource.md`） **[Inferred]** | 文件操作的文件名来自用户输入且未过滤`CON`/`NUL`/`/dev/`等虚拟资源名 | 所有接受用户输入作为文件名的场景(Windows设备名/Linux设备文件) | 程序未识别和过滤标识虚拟资源的特殊文件名，导致非预期设备操作 | UVS-FILE-VIRTUAL-RESOURCE | FIX-FILE-VIRTUAL-01 | ATK-FILE-VIRTUAL-01 |
| VULN-FILE-SEARCHPATH-01（`file-untrusted-search-path.md`） **[Inferred]** | `subprocess.call`/`LoadLibrary`/`dlopen`/`import`无绝对路径且PATH含当前目录 | C/C++/Python/Java/Go/Rust等所有加载外部代码/库的语言 | 加载可执行文件或库的搜索路径包含不可信/可控制目录，攻击者可植入恶意代码 | UVS-FILE-UNTRUSTED-SEARCH-PATH | FIX-FILE-SEARCHPATH-01 | ATK-FILE-SEARCHPATH-01 |
| VULN-FILE-TEMPFILE-01（`file-insecure-temp.md`） **[Inferred]** | 临时文件名可预测(固定前缀+用户ID/时间戳)；使用`mktemp`而非`mkstemp`；权限过宽 | C/Python/Java/Go/Rust等所有创建临时文件的语言 | 临时文件名可预测、权限过宽或使用不安全创建方式，导致竞争/未授权访问 | UVS-FILE-INSECURE-TEMP | FIX-FILE-TEMPFILE-01 | ATK-FILE-TEMPFILE-01 |
| VULN-INPUT-VALIDATION-01（`input-validation-failure.md`） **[Inferred，抽象根模式]** | 外部输入到达危险操作且路径上无输入验证；无法匹配更具体子模式时fallback | 不限语言/框架（抽象根模式） | 系统未对外部输入进行充分验证，导致不符合预期的数据进入后续处理流程 | UVS-INPUT-VALIDATION-FAILURE | FIX-INPUT-VALIDATION-01 | 不适用（抽象根模式） |
| VULN-INPUT-XML-01（`input-xml-validation.md`） **[Inferred]** | XML解析器接受外部输入且未禁用外部实体/DTD/实体扩展 | Java/Python/PHP/.NET/C/C++/Rust等所有解析XML的语言 | XML输入未经Schema/DTD结构验证且解析器未禁用外部实体/实体扩展 | UVS-INPUT-XML-VALIDATION | FIX-INPUT-XML-01 | ATK-INPUT-XML-01 |
| VULN-INPUT-MISPARSE-01（`input-misinterpretation.md`） **[Inferred]** | 同一输入经过多层解析(代理+后端)；安全检查和使用使用不同层的解析结果 | 所有有多层解析的场景(Web代理/服务器/API网关) | 不同处理阶段/组件对同一输入使用不同解析规则，安全检查基于错误解析结果而失效 | UVS-INPUT-MISINTERPRETATION | FIX-INPUT-MISPARSE-01 | ATK-INPUT-MISPARSE-01 |
| VULN-INPUT-SPECELEM-01（`input-special-element-handling.md`） **[Inferred]** | `split()`/解析后直接访问特定位置字段而不检查解析结果结构完整性 | 不限语言/框架(CSV/JSON/协议解析) | 输入验证未检查特殊元素是否存在/是否多余/是否一致，导致结构异常输入通过验证 | UVS-INPUT-SPECIAL-ELEMENT-HANDLING | FIX-INPUT-SPECELEM-01 | ATK-INPUT-SPECELEM-01 |
| VULN-INPUT-CASE-01（`input-case-sensitivity.md`） **[Inferred]** | 安全检查大小写敏感但后续操作(文件系统/数据库)大小写不敏感(或反之) | Windows文件系统/数据库COLLATION/HTTP等有大小写敏感差异的场景 | 安全检查和数据处理对大小写处理方式不一致，攻击者通过大小写变体绕过检查 | UVS-INPUT-CASE-SENSITIVITY | FIX-INPUT-CASE-01 | ATK-INPUT-CASE-01 |
| VULN-INPUT-COLLAPSE-01（`input-data-collapse.md`） **[Inferred]** | 安全检查在`unicodedata.normalize`/`toLowerCase`/编码转换之前执行 | Python(unicodedata)/Java(Normalizer)/数据库(Unicode COLLATION) | 安全检查在数据转换前执行，多个输入在Unicode规范化/大小写折叠后坍缩为同一不安全值 | UVS-INPUT-DATA-COLLAPSE | FIX-INPUT-COLLAPSE-01 | ATK-INPUT-COLLAPSE-01 |
| VULN-INPUT-HANDLING-01（`input-handling-failure.md`） **[Inferred]** | 输入处理函数假设特定类型/值但无`isinstance`/边界检查/异常处理 | 动态语言(Python/JS)更易出现；静态语言边界值/缺失参数仍可能未处理 | 输入处理逻辑未覆盖所有可能的值/参数/结构变体/数据类型，边界情况未被正确处理 | UVS-INPUT-HANDLING-FAILURE | FIX-INPUT-HANDLING-01 | ATK-INPUT-HANDLING-01 |
| VULN-INPUT-REGEX-01（`input-incorrect-regex.md`） **[Inferred]** | 验证输入的正则无`^`/`$`锚点；用`*`允许空；含嵌套量词`(a+)+`导致ReDoS | Python(re)/Java(regex)/JS(RegExp)/Go(regexp)/Rust(regex)/PHP(PCRE) | 验证输入的正则表达式逻辑错误（过于宽松/过于严格/无锚点/ReDoS风险） | UVS-INPUT-INCORRECT-REGEX | FIX-INPUT-REGEX-01 | ATK-INPUT-REGEX-01 |
| VULN-INPUT-INVALIDSTRUCT-01（`input-invalid-structure-handling.md`） **[Inferred]** | `json.loads`/`ElementTree.parse`/`csv.reader`无try-catch；使用宽松模式解析 | 不限语言(JSON/XML/CSV/协议解析) | 解析器未正确识别和处理语法上无效的数据结构，导致崩溃或非预期行为 | UVS-INPUT-INVALID-STRUCTURE-HANDLING | FIX-INPUT-INVALIDSTRUCT-01 | ATK-INPUT-INVALIDSTRUCT-01 |
| VULN-CONC-RACE-01（`conc-race-condition-toctou.md`） **[Proposed]** | "先检查后使用"模式且检查与使用间无锁/事务/原子操作 | Python/Java/Go/C/C++/Node.js等所有支持并发的语言 | TOCTOU竞态条件——检查与使用之间缺乏原子性 | UVS-CONC-RACE-CONDITION | FIX-CONC-RACE-01 | ATK-CONC-RACE-01 |
| VULN-CONC-LOCKING-01（`conc-improper-locking.md`） **[Proposed]** | lock.acquire()后无try-finally/with/RAII释放；多锁获取顺序不一致；空同步块 | Python/Java/C++/Go/C等所有提供锁机制的语言 | 锁机制使用不当——未在异常路径释放/死锁/粒度不当 | UVS-CONC-IMPROPER-LOCKING | FIX-CONC-LOCKING-01 | ATK-CONC-LOCKING-01 |
| VULN-EXC-UNCHECKED-01（`exc-unchecked-return-value.md`） **[Proposed]** | malloc/fopen返回值未检查NULL；Go的error返回值被_忽略；验证函数返回值未检查 | C/C++/Go/Python/Java等所有有可失败函数调用的语言 | 返回值/错误条件未检查——函数失败后继续执行危险操作 | UVS-EXC-IMPROPER-CHECK | FIX-EXC-UNCHECKED-01 | ATK-EXC-UNCHECKED-01 |
| VULN-EXC-SWALLOWED-01（`exc-swallowed-exception.md`） **[Proposed]** | except: pass/空catch块；且catch块后有安全相关操作继续执行 | Python/Java/JavaScript/C#/PHP等所有有异常处理的语言 | 异常被吞没——捕获后空处理，安全控制被静默绕过 | UVS-EXC-IMPROPER-HANDLING | FIX-EXC-SWALLOWED-01 | ATK-EXC-SWALLOWED-01 |
| VULN-EXC-FAILOPEN-01（`exc-fail-open-on-error.md`） **[Proposed]** | 安全检查的catch/错误分支使用默认用户/返回true/创建会话 | 不限语言/框架，任何有安全检查逻辑的代码 | 失败时fail-open——安全检查失败时默认允许而非拒绝 | UVS-EXC-INSECURE-FAILURE | FIX-EXC-FAILOPEN-01 | ATK-EXC-FAILOPEN-01 |
| VULN-EXC-GENERIC-01（`exc-generic-handling-failure.md`） **[Proposed，抽象根模式]** | 异常处理机制缺失或不当；无法匹配更具体子模式时的fallback | 不限语言/框架（抽象根模式） | 异常条件处理失效——异常域根模式 | UVS-EXC-FAILURE | 不适用（抽象根模式） | 不适用（抽象根模式） |
| VULN-CALC-INTOVERFLOW-01（`calc-integer-overflow.md`） **[Proposed]** | malloc(len*sizeof)/memcpy的乘法无溢出检查；除法无除零检查 | C/C++/Java/Go/Python等所有有数值计算的语言 | 整数溢出/计算错误——缓冲区大小计算溢出/除零 | UVS-CALC-FAILURE | FIX-CALC-INTOVERFLOW-01 | ATK-CALC-INTOVERFLOW-01 |
| VULN-CALC-COMPARE-01（`calc-comparison-error.md`） **[Proposed]** | Java中==比较字符串引用；C中strcmp返回值判断错误；弱类型==比较 | Java/C/C++/JavaScript/PHP等所有有比较操作的语言 | 比较错误——引用比较/类型不匹配导致安全决策偏差 | UVS-CALC-COMPARISON-FAILURE | FIX-CALC-COMPARE-01 | ATK-CALC-COMPARE-01 |
| VULN-CALC-INCOMPLETE-01（`calc-incomplete-comparison.md`） **[Proposed]** | len(password)==len(stored)只比较长度；strncmp只比较前N字节 | 不限语言/框架，密码比较/令牌验证/权限检查场景 | 不完整比较——只比较部分因子导致安全决策绕过 | UVS-CALC-INCOMPLETE-COMPARISON | FIX-CALC-INCOMPLETE-01 | ATK-CALC-INCOMPLETE-01 |
| VULN-CALC-LENGTH-01（`calc-length-parameter-mismatch.md`） **[Proposed]** | memcpy(buf,data,len)的len来自网络包长度字段且未验证一致性 | C/C++/Python(ctypes)/Go/Rust(unsafe)等所有有缓冲区操作的语言 | 长度参数不一致——长度字段与实际数据不匹配导致过读/溢出 | UVS-CALC-LENGTH-PARAMETER | FIX-CALC-LENGTH-01 | ATK-CALC-LENGTH-01 |
| VULN-PROT-BYPASS-01（`prot-protection-bypass.md`） **[Proposed，抽象根模式]** | 保护机制缺失或可绕过；无法匹配更具体子模式时的fallback | 不限语言/框架（抽象根模式） | 保护机制失效——保护域根模式 | UVS-PROT-FAILURE | 不适用（抽象根模式） | 不适用（抽象根模式） |
| VULN-PROT-CLIENTSIDE-01（`prot-client-side-enforcement.md`） **[Proposed]** | 前端有验证/授权/过滤但服务端无相同验证；客户端隐藏管理按钮但API无授权 | Web前端(JS)/移动App/Electron，服务端框架需检查对应验证 | 安全控制仅在客户端执行——绕过客户端后服务端无对应控制 | UVS-PROT-CLIENT-SIDE-ENFORCEMENT | FIX-PROT-CLIENTSIDE-01 | ATK-PROT-CLIENTSIDE-01 |
| VULN-PROT-OBSCURITY-01（`prot-obscurity-reliance.md`） **[Proposed]** | 无认证的隐藏管理面板；自定义秘密算法替代标准密码学；混淆代码作为唯一安全控制 | 不限语言/框架，隐藏URL/自定义算法/代码混淆场景 | 依赖隐蔽性——安全保护依赖实现细节隐蔽而非密码学强度 | UVS-PROT-OBSCURITY-RELIANCE | FIX-PROT-OBSCURITY-01 | ATK-PROT-OBSCURITY-01 |
| VULN-PROT-SINGLEFACTOR-01（`prot-single-factor-reliance.md`） **[Proposed]** | 认证仅检查密码无MFA/2FA；特权操作仅要求登录无step-up认证 | 不限语言/框架，认证/特权操作/敏感交易场景 | 单因素依赖——关键安全决策仅依赖单一因素，被攻破后无额外保障 | UVS-PROT-SINGLE-FACTOR-RELIANCE | FIX-PROT-SINGLEFACTOR-01 | ATK-PROT-SINGLEFACTOR-01 |
| VULN-PROT-GUESSABLE-01（`prot-guessable-challenge.md`） **[Proposed]** | 简单数学CAPTCHA(1+5=?)；答案空间过小；固定模板无随机化 | Web应用(自定义CAPTCHA)、移动应用、API反自动化场景 | 可猜测验证挑战——CAPTCHA复杂度不足，自动化程序能以高概率通过 | UVS-PROT-GUESSABLE-CHALLENGE | FIX-PROT-GUESSABLE-01 | ATK-PROT-GUESSABLE-01 |
| VULN-PROT-ADMINCTRL-01（`prot-admin-control-missing.md`） **[Proposed]** | 安全设置硬编码无法通过管理界面修改；无审计日志查看界面 | 不限语言/框架，SaaS/企业应用/嵌入式设备的管理接口 | 管理员控制缺失——安全设置不可配置/安全事件不可监控(治理性信号) | UVS-PROT-ADMIN-CONTROL-FAILURE | FIX-PROT-ADMINCTRL-01 | 不适用（无独立活攻击面） |
| VULN-RES-UNCONTROLLED-01（`res-uncontrolled-consumption.md`） **[Inferred]** | 端点接受外部输入进行资源密集型操作但无大小/频率/连接数限制 | Python/Java/Node.js/Go/PHP等所有Web框架 | 资源消耗无限制——无配额/速率/大小约束导致DoS | UVS-RES-UNCONTROLLED-CONSUMPTION | FIX-RES-CONSUMPTION-LIMIT-01 | ATK-RES-CONSUMPTION-01 |
| VULN-RES-RELEASE-01（`res-improper-release.md`） **[Inferred]** | 资源获取调用未用with/try-with-resources/RAII/defer包裹且有多个退出路径 | Python/Java/C++/Go/PHP/Node.js等所有需显式释放资源的语言 | 资源释放缺失或不当——文件/连接/句柄泄漏 | UVS-RES-IMPROPER-RELEASE | FIX-RES-RELEASE-01 | 不适用（无独立活攻击面——资源生命周期/可靠性缺陷） |
| VULN-RES-ITERATION-01（`res-excessive-iteration.md`） **[Inferred]** | while True/for(;;)无条件循环或循环条件变量可能不被更新且无迭代上限 | 所有语言——循环结构是通用原语 | 循环终止条件不正确或无上限——过度迭代/无限循环DoS | UVS-RES-EXCESSIVE-ITERATION | FIX-RES-ITERATION-01 | ATK-RES-ITERATION-01 |
| VULN-RES-RECURSION-01（`res-uncontrolled-recursion.md`） **[Inferred]** | 递归函数无max_depth限制且深度受外部输入（嵌套JSON/XML/树）影响 | Python/Java/C/C++/JavaScript/Go等所有支持递归的语言 | 递归深度无限制——栈溢出/递归失控DoS | UVS-RES-UNCONTROLLED-RECURSION | FIX-RES-RECURSION-01 | ATK-RES-RECURSION-01 |
| VULN-RES-COMPLEXITY-01（`res-inefficient-complexity.md`） **[Inferred]** | 回溯正则(嵌套量词)/嵌套循环O(n²)/指数算法且无输入上限/超时 | Python re/Java regex/JS RegExp/PHP preg/Go regexp等 | 算法复杂度未受控制——二次/指数级DoS(ReDoS) | UVS-RES-INEFFICIENT-COMPLEXITY | FIX-RES-COMPLEXITY-01 | ATK-RES-COMPLEXITY-01 |
| VULN-RES-FREQUENCY-01（`res-interaction-frequency.md`） **[Inferred]** | 敏感端点(认证/密码重置/OTP)无速率限制中间件/装饰器 | Python/Java/Node.js/Go/PHP等所有Web框架 | 交互频率无限制——速率/操作次数无约束 | UVS-RES-INTERACTION-FREQUENCY-UNCONTROLLED | FIX-RES-FREQUENCY-01 | ATK-RES-FREQUENCY-01 |
| VULN-RES-POOL-01（`res-insufficient-pool.md`） **[Inferred]** | 连接池/线程池容量配置过小(硬编码小常量)且无获取超时/降级 | Python SQLAlchemy/Java HikariCP/Node.js pg/Go database/sql等 | 资源池容量规划不足——连接池/线程池过小 | UVS-RES-INSUFFICIENT-POOL | FIX-RES-POOL-01 | 不适用（无独立活攻击面——资源生命周期/可靠性缺陷） |
| VULN-RES-UAF-01（`res-use-after-release.md`） **[Inferred]** | 资源释放后引用未置空且有后续使用；未用智能指针/RAII | C/C++(最严重)/Python/Java/Go/Rust(unsafe可绕过)等 | 释放后使用——Use-After-Free/悬垂引用 | UVS-RES-USE-AFTER-RELEASE | FIX-RES-UAF-01 | ATK-RES-UAF-01 |
| VULN-RES-REFCOUNT-01（`res-reference-count-error.md`） **[Inferred]** | 手动引用计数(retain/release)配对不完整或并发场景非原子更新 | C/C++/Obj-C/Swift ARC/Rust Rc/Arc/Linux kref等 | 引用计数更新不完整——获取/释放配对缺失 | UVS-RES-REFERENCE-COUNT-ERROR | FIX-RES-REFCOUNT-01 | 不适用（无独立活攻击面——资源生命周期/可靠性缺陷） |
| VULN-RES-LIFETIME-01（`res-lifetime-failure.md`） **[Inferred]** | 资源生命周期管理存在缺陷(初始化/使用/释放阶段违反) | 不限语言/框架（支柱级语义框架） | 资源生命周期管理缺失——支柱级引用子UVS模式 | UVS-RES-LIFETIME-FAILURE | 不适用（支柱级） | 不适用（支柱级） |
| VULN-RES-INIT-01（`res-initialization-failure.md`） **[Inferred]** | malloc/栈变量分配后未初始化即被使用；Go nil map/slice未make | C/C++(最严重)/Python/Java/Go/Rust等 | 初始化逻辑缺失或错误——未初始化使用 | UVS-RES-INITIALIZATION-FAILURE | FIX-RES-INIT-01 | 不适用（无独立活攻击面——资源生命周期/可靠性缺陷） |
| VULN-RES-MULTIOP-01（`res-multiple-operation.md`） **[Inferred]** | 单次操作(free/commit/支付)无幂等性检查/状态守卫且有重试/并发路径 | 不限语言/框架——支付/事务/初始化等单次操作 | 操作唯一性约束缺失——重复执行单次操作 | UVS-RES-MULTIPLE-OPERATION | FIX-RES-MULTIOP-01 | 不适用（无独立活攻击面——资源生命周期/可靠性缺陷） |
| VULN-RES-PHASE-01（`res-wrong-phase-operation.md`） **[Inferred]** | 资源操作未验证当前生命周期阶段(已关闭后操作/已提交后回滚) | 不限语言/框架——数据库事务/连接/文件状态机 | 资源生命周期阶段验证缺失——错误阶段操作 | UVS-RES-WRONG-PHASE-OPERATION | FIX-RES-PHASE-01 | 不适用（无独立活攻击面——资源生命周期/可靠性缺陷） |
| VULN-RES-DUPID-01（`res-duplicate-identifier.md`） **[Inferred]** | 标识符使用不保证唯一的生成机制(自增/时间戳)且无UNIQUE约束 | 不限语言/框架——数据库自增ID/时间戳ID/会话ID | 资源标识符唯一性约束缺失——重复标识符 | UVS-RES-DUPLICATE-IDENTIFIER | FIX-RES-DUPID-01 | 不适用（无独立活攻击面——资源生命周期/可靠性缺陷） |
| VULN-RES-EMERGENT-01（`res-emergent-resource.md`） **[Inferred]** | 操作过程中产生临时文件/缓存/派生数据但无清理/访问控制/TTL | 不限语言/框架——tempfile/缓存/临时表 | 涌现资源管理缺失——中间/临时资源未纳入管理 | UVS-RES-EMERGENT-RESOURCE | FIX-RES-EMERGENT-01 | 不适用（无独立活攻击面——资源生命周期/可靠性缺陷） |
| VULN-CFLOW-OPENREDIRECT-01（`cflow-open-redirect.md`） **[Inferred]** | redirect()参数来自return_url/next/redirect_uri且无is_safe_url验证 | Python/Java/Node.js/PHP/Go等所有支持HTTP重定向的框架 | 重定向目标未验证——开放重定向 | UVS-CFLOW-OPEN-REDIRECT | FIX-CFLOW-OPENREDIRECT-01 | ATK-CFLOW-OPENREDIRECT-01 |
| VULN-CFLOW-INSUFFICIENT-01（`cflow-insufficient.md`） **[Inferred]** | 控制流管理存在缺陷(循环边界/条件分支/作用域) | 不限语言/框架（支柱级语义框架） | 控制流管理缺失——支柱级引用子UVS模式 | UVS-CFLOW-INSUFFICIENT | 不适用（支柱级） | 不适用（支柱级） |
| VULN-CFLOW-IMPL-01（`cflow-incorrect-implementation.md`） **[Inferred]** | 安全关键条件恒真/恒假/赋值代替比较(=vs==) | C/C++/Python/Java/JavaScript等 | 控制流逻辑实现错误——死代码/恒真恒假条件 | UVS-CFLOW-INCORRECT-IMPLEMENTATION | FIX-CFLOW-IMPL-01 | 不适用（无独立活攻击面——控制流逻辑缺陷） |
| VULN-CFLOW-ORDER-01（`cflow-incorrect-behavior-order.md`） **[Inferred]** | 授权检查在业务逻辑之后执行/输入验证在使用之后 | 不限语言/框架——中间件/装饰器顺序 | 安全关键操作顺序错误——行为顺序不正确 | UVS-CFLOW-INCORRECT-BEHAVIOR-ORDER | FIX-CFLOW-ORDER-01 | 不适用（无独立活攻击面——控制流逻辑缺陷） |
| VULN-CFLOW-CALL-01（`cflow-function-call-error.md`） **[Inferred]** | 安全函数调用参数数量/类型/顺序与签名不匹配 | C/C++(变参)/Python(默认参数省略)/Java(重载选择)/JS(无类型检查) | 函数调用参数与签名不一致——参数错误 | UVS-CFLOW-FUNCTION-CALL-ERROR | FIX-CFLOW-CALL-01 | 不适用（无独立活攻击面——控制流逻辑缺陷） |
| VULN-CFLOW-SCOPE-01（`cflow-incorrect-scoping.md`） **[Inferred]** | 安全变量在过宽作用域暴露/变量遮蔽/异常catch过宽 | Python(global)/JavaScript(var vs let)/Java(catch范围)等 | 作用域管理不正确——变量在错误作用域可见 | UVS-CFLOW-INCORRECT-SCOPING | FIX-CFLOW-SCOPE-01 | 不适用（无独立活攻击面——控制流逻辑缺陷） |
| VULN-CFLOW-WORKFLOW-01（`cflow-workflow-enforcement-failure.md`） **[Inferred]** | 多步操作后续步骤无前置步骤状态验证/步骤状态由客户端传递 | 不限语言/框架——向导式注册/电商/审批流程 | 工作流步骤验证缺失——多步操作跳步/乱序 | UVS-CFLOW-WORKFLOW-ENFORCEMENT-FAILURE | FIX-CFLOW-WORKFLOW-01 | ATK-CFLOW-WORKFLOW-01 |
| VULN-INFO-EXPOSURE-01（`info-sensitive-exposure.md`） **[Inferred]** | API序列化to_dict()含敏感字段/错误信息含堆栈/日志记录凭证 | Python/Java/Node.js/PHP等所有Web框架 | 敏感信息未授权暴露——API响应/错误/日志泄露 | UVS-INFO-SENSITIVE-EXPOSURE | FIX-INFO-EXPOSURE-01 | ATK-INFO-EXPOSURE-01 |
| VULN-INFO-OBSERVABLE-01（`info-observable-discrepancy.md`） **[Inferred]** | 认证端点区分"用户不存在"/"密码错误"；密码比较非常量时间 | 不限语言/框架——认证/用户查询/资源查询端点 | 可观察差异导致侧信道推断——时序/响应/行为差异 | UVS-INFO-OBSERVABLE-DISCREPANCY | FIX-INFO-OBSERVABLE-01 | ATK-INFO-OBSERVABLE-01 |
| VULN-INFO-STORAGE-01（`info-insecure-storage.md`） **[Inferred]** | 配置文件明文存储密码/源码硬编码API密钥/数据库明文PII | 不限语言/框架——配置/源码/数据库/环境变量 | 敏感信息存储保护缺失——明文/弱保护存储 | UVS-INFO-INSECURE-STORAGE | FIX-INFO-STORAGE-01 | 不适用（无独立活攻击面——被动信息保护缺陷） |
| VULN-INFO-LOSS-01（`info-loss-or-omission.md`） **[Inferred]** | 安全相关数据(审计日志/安全头/完整性校验)在传输存储中被截断 | 不限语言/框架——日志/安全头/完整性校验 | 信息完整性保护缺失——数据截断/遗漏/丢失 | UVS-INFO-LOSS-OR-OMISSION | FIX-INFO-LOSS-01 | 不适用（无独立活攻击面——被动信息保护缺陷） |
| VULN-INFO-REMOVAL-01（`info-removal-failure.md`） **[Inferred]** | 敏感数据使用后仅删除引用未覆盖内存/仅删除文件未安全擦除 | C/C++(free未memset)/Python/Java/文件系统等 | 敏感数据清除逻辑缺失——残留/未覆盖 | UVS-INFO-REMOVAL-FAILURE | FIX-INFO-REMOVAL-01 | 不适用（无独立活攻击面——被动信息保护缺陷） |
| VULN-INFO-LEAK-01（`info-resource-leak.md`） **[Inferred]** | 错误信息含内部路径/响应含内部服务地址/重定向到内部端点 | 不限语言/框架——错误处理/响应构造/路径输出 | 跨域资源传输控制缺失——私有资源泄漏到新域 | UVS-INFO-RESOURCE-LEAK | FIX-INFO-LEAK-01 | 不适用（无独立活攻击面——被动信息保护缺陷） |
| VULN-INFO-COVERT-01（`info-covert-channel.md`） **[Inferred]** | 高安全操作影响共享资源状态被低安全操作观察；无常量时间操作 | 不限语言/框架——共享缓存/内存/文件系统时序 | 隐蔽信道检测和控制缺失——时序/资源/状态侧信道 | UVS-INFO-COVERT-CHANNEL | FIX-INFO-COVERT-01 | ATK-INFO-COVERT-01 |
| VULN-AC-FAILURE-01（`general-access-control-failure.md`） **[Inferred]** | 访问控制机制整体缺失或失效，且无法归入更具体子模式 | 不限语言/框架（访问控制支柱级模式） | 访问控制整体失效的支柱级检测模式 | UVS-AC-FAILURE | 不适用（支柱级） | 不适用（支柱级） |
| VULN-AC-PRIVILEGE-01（`improper-privilege-dropping.md`） **[Inferred]** | setgid/setuid顺序错误、返回值未检查或只放弃部分特权 | Unix/Linux系统编程、容器入口与守护进程 | 权限放弃不完整导致进程保留可恢复特权 | UVS-AC-PRIVILEGE-MANAGEMENT-FAILURE | FIX-AC-PRIVILEGE-01 | ATK-AC-PRIVILEGE-01 |
| VULN-AC-PERM-ASSIGN-01（`overly-permissive-default-permissions.md`） **[Inferred]** | 文件或配置创建时依赖过宽默认mode/umask | Unix/Linux文件系统及跨平台文件API | 关键资源默认权限过宽，可被非预期主体读取或修改 | UVS-AC-PERMISSION-ASSIGNMENT-ERROR | FIX-AC-PERM-ASSIGN-01 | ATK-AC-PERM-READ-01 |
| VULN-AC-PHYSICAL-01（`physical-access-control-gaps.md`） **[Inferred]** | 调试接口、USB端口或机箱缺少生产环境物理保护 | 硬件、IoT、嵌入式与终端设备 | 物理访问控制缺失使本地攻击者可接触敏感接口 | UVS-AC-PHYSICAL-ACCESS-FAILURE | FIX-AC-PHYSICAL-01 | ATK-AC-PHYSICAL-01 |
| VULN-AC-OWNERSHIP-01（`unverified-ownership.md`） **[Inferred]** | 资源操作仅校验存在性或ID，未校验当前主体所有权 | Web/API/多租户资源访问 | 资源所有权未验证，非所有者可操作他人资源 | UVS-AC-OWNERSHIP-FAILURE | FIX-AC-OWNERSHIP-01 | ATK-AC-OWNERSHIP-01 |
| VULN-AUTHZ-OBJECT-LEVEL-01（`object-level-authorization-missing.md`） **[Inferred]** | 对象ID可控且查询或更新未绑定当前主体/租户 | Web/API/ORM/多租户应用 | 对象级授权缺失导致IDOR或跨租户访问 | UVS-AC-AUTHORIZATION-FAILURE | FIX-AUTHZ-OBJECT-LEVEL-01 | ATK-AUTHZ-OBJECT-CROSS-01 |
| VULN-AUTHN-BYPASS-01（`authentication-bypass.md`） **[Inferred]** | 密码验证缺失、条件逻辑错误或认证结果未被消费 | Web/API/桌面/移动认证流程 | 认证逻辑可被绕过 | UVS-AUTHN-FAILURE | FIX-AUTHN-COMPLETE-01 | ATK-AUTHN-BYPASS-01 |
| VULN-AUTHN-NO-RATELIMIT-01（`missing-brute-force-protection.md`） **[Inferred]** | 登录/OTP端点无频率限制、延迟或合理锁定 | 所有认证端点 | 认证暴力破解防护缺失 | UVS-AUTHN-BRUTE-FORCE-FAILURE | FIX-AUTHN-RATELIMIT-01 | ATK-AUTHN-BRUTE-01 |
| VULN-AUTHN-LOCKOUT-01（`overly-strict-account-lockout.md`） **[Inferred]** | 少量失败即长期锁定且攻击者可指定受害账户 | 所有账户锁定实现 | 过严锁定策略可被滥用为拒绝服务 | UVS-AUTHN-LOCKOUT-IMPROPER | FIX-AUTHN-LOCKOUT-01 | ATK-AUTHN-LOCKOUT-DOS-01 |
| VULN-AUTHN-PASSHASH-01（`pass-the-hash-credential-confusion.md`） **[Inferred]** | 服务端接受客户端提交的密码哈希作为等价凭证 | 自定义认证、遗留协议与API | 密码哈希被错误当作可重放凭证 | UVS-AUTHN-HASH-AS-CREDENTIAL | FIX-AUTHN-PASSHASH-01 | ATK-AUTHN-PASSHASH-01 |
| VULN-AUTHN-CRED-PROTECT-01（`plaintext-credential-storage.md`） **[Inferred]** | 凭证明文存储或写入日志/API响应 | 所有凭证存储与处理流程 | 凭证保护失效导致直接泄露 | UVS-AUTHN-CREDENTIAL-PROTECTION-FAILURE | FIX-AUTHN-CRED-PROTECT-01 | ATK-AUTHN-CRED-LEAK-01 |
| VULN-AUTHN-INSECURE-ID-01（`predictable-session-identifier.md`） **[Inferred]** | Session ID/Token使用自增、时间戳或弱随机生成 | 有状态会话与令牌系统 | 可预测安全标识符可被枚举或预计算 | UVS-AUTHN-INSECURE-ID-MECHANISM | FIX-AUTHN-SECURE-ID-01 | ATK-AUTHN-ID-PREDICT-01 |
| VULN-AUTHN-SESSION-LIFECYCLE-01（`insufficient-session-expiration.md`） **[Inferred]** | 会话无合理超时，或登出/改密后服务端未失效 | 有状态会话与令牌系统 | 会话生命周期管理不足允许过期会话复用 | UVS-AUTHN-SESSION-LIFECYCLE-FAILURE | FIX-AUTHN-SESSION-LIFECYCLE-01 | ATK-AUTHN-STALE-SESSION-01 |
| VULN-AUTHN-WEAK-CRED-01（`weak-credential-policy.md`） **[Inferred]** | 允许弱口令、默认凭证或硬编码凭证 | 所有认证与凭证配置场景 | 弱凭证策略降低认证强度 | UVS-AUTHN-WEAK-CREDENTIALS | FIX-AUTHN-WEAK-CRED-01 | ATK-AUTHN-WEAK-CRED-01 |

## 3. 单个知识条目内部结构规范

**文件组织**：每个知识条目是独立小文件，复用#16已定的"小文件"哲学，不做大而全的单一文件。分类粒度（是否按语言/CWE大类拆`<category>/`子目录）当前未定（#16/#24均已声明留待实际编写条目时确定），条目数量较少时可直接放在`vuln-patterns/`根目录下；增长到需要分类时，按第7节的规模应对方案拆分。

**模板**：编写新条目时参考 [`_template.md`](_template.md)（模板不计入正式知识条目，不构成检测能力）。

**内部结构**：按**Source / Propagation / Sanitizer / Sink**四段为骨架组织，对应#4（验证确认）已确立的六项验收基线字段需求。2026-08-09知识建设批次（KBATCH-001）后，模板扩展为以下完整章节（原有四段保留，新增章节补充语义完整性和可执行性）：

| 条目内部段落 | 对应#4六项验收基线 | 该段应记录的内容 |
|---|---|---|
| 根因与安全不变量 | — | 根本原因和被违反的安全不变量 |
| 外部分类映射 | — | CWE/CAPEC/OWASP引用 |
| 适用Surface与Entry | — | 本体概念引用，适用攻击面和入口 |
| Source | 可控性（controllable） | 这条模式关注的输入源特征——什么样的入口点/参数使这个输入被视为攻击者可控 |
| Propagation / Transformation / Storage | 可达性（reachable）+ 传播完整性（propagatable） | 从Source到Sink之间典型的传播路径形态——经过哪些中间调用/数据结构变换，路径连不连得上 |
| Guard | 传播完整性 | 守卫控制的存在/缺失/绕过状态 |
| Sanitizer | 传播完整性（propagatable）的净化检查环节 | 这条路径上本该存在、或本该被绕过的净化/校验逻辑——命中此模式的关键判据往往是"该有的Sanitizer缺失或可被绕过" |
| Encoder | 传播完整性 | 输出上下文编码是否正确 |
| Sink / State Transition / Resource Consumption | 可利用性（exploitable）+ 影响成立（impact） | 危险操作本身是什么，以及触发后典型会造成什么后果 |
| 非污点语义模型（如适用） | 传播完整性 | 授权/业务逻辑/并发/密码学/配置/资源/内存安全等非污点模型 |
| 可执行发现步骤 | — | 逐步写明定位流程，供#3模式驱动发现直接执行 |
| 正例 | — | 命中本模式的代码示例 |
| 负例 | — | 不命中本模式的代码示例 |
| 排除条件 | — | 不应命中本模式的场景 |
| 业务逻辑提示 | — | 业务逻辑相关注意事项 |
| 横向差异提示 | — | 横向差异发现机制如何辅助定位 |
| 兄弟变体 | — | 同类变体及其差异 |
| 验证方法 | — | #4验证确认阶段如何验证 |
| 反证方法 | — | #4验证确认阶段如何证伪 |
| Observable Oracle | — | 命中后可观察到的后果 |
| 影响与前置权限 | — | 影响类型、前置权限、暴露范围 |
| 生态映射引用 | — | 生态映射条目引用 |
| 攻击模式引用 | — | attack-patterns条目引用 |
| 修复模式引用 | — | fix-patterns条目引用 |
| 消费Skill | — | 消费此条目的Skill列表 |
| 来源与证据 | — | 证据来源、引用分级、证据局限 |
| 成熟度及版本历史 | — | 版本变更和成熟度状态 |

条目文件不需要重复记录"可复现性（reproducible）"——这是#4验证阶段、#6可利用性证明阶段自己的职责，不是知识条目该预先写死的内容。

**UVS关联**：每个漏洞模式条目应关联对应的统一漏洞语义（UVS-\*），通过`unified_semantic_refs`字段引用。UVS关联不等于模式驱动发现——只有命中具有`discoverable=complete`证据的vuln-pattern才能称模式驱动发现。

## 4. 强制显式查阅纪律（核心纪律，不得含糊）

- "要不要查、查了没有"不能交给#3自由裁量。#3的模式驱动发现机制消费本目录时，产出必须显式写明**查了哪个条目ID**（对应`candidate-discovery/SKILL.md`已落地的`discovery_reasoning_note`字段要求）。
- 查不到匹配条目时，必须显式写**"未匹配，可能是新模式"**，不能用含糊的表述（如直接跳过不提、或含混地说"未发现已知模式"而不点明"未匹配"这个结论本身）代替。
- 引用的条目ID必须可被机械核对——是否真实存在于本索引表格里（应用#17已确立的T2机械核对能力）。核对的对象是"引用的ID是否存在"这件事本身，不涉及"这次判断对不对"，后者仍是#3/#4自己的职责。核对由宿主Agent按#17 T2机械核对能力执行——检查ID是否存在于本索引表格中即可，不需要GenSource自建验证程序。本文件锁定"必须可核对"这条原则。

## 5. 引用分级

复用#7/#11已确立的**Observed / Inferred / Proposed**三段式标签，不新造标签体系。在本目录场景下的含义：

- **Observed**：目标代码中确实观察到与该条目"触发信号"列完全吻合的信号（如确实读到了未参数化拼接的字符串）。
- **Inferred**：结构上部分吻合，基于代码结构推断认为适用，尚未逐一核实条目内Source/Propagation/Sanitizer/Sink每个维度。
- **Proposed**：条目本身来自尚未充分验证的新增知识（例如#16持续学习流程产出但尚未经人工复核的条目），消费方不能因为"命中了"就贸然当作Observed对待。

**标注归属**：这个分级标注写在#3产出的候选记录里（描述"这次具体审计怎么用这条知识"），不是本索引文件自身的字段——本索引文件只描述"这个条目是什么"，不描述"某次具体引用的可信程度"。

## 6. 不采纳向量/混合检索

复用06号早期跨竞品打分框架已确立、24号（#15）再次确认仍有效的结论：**F1（纯Markdown小文件+表格索引）为基座不动摇，F2（向量/混合检索）明确不采纳**。

**元星刃反例**（06号/24号已引用）：元星刃建成了CWE-7全量XML+BM25/Chroma混合检索能力，但8个worker的system prompt完全没有引用检索结果——"知识库与审计流程完全脱钩"（`09-yuanxingren.md`§9）。这证明"有检索能力"和"检索能力真正驱动判断"是两件不同的事：向量检索的价值高度依赖工程实现是否真的把检索结果接入判断链路，不能想当然认为"上了向量库就变强"。

本项目规模不到需要向量检索的量级（复用#15/#12已确认的判断），本目录索引始终保持"表格化+人工/agent扫一眼就能判断该不该细看"的哲学，不引入语义相似度检索或混合检索基础设施，避免重复元星刃"建成了但没人真正用"的脱钩代价。

## 7. 索引规模过大时的应对

复用#12（`docs/research/decision/25-category12-scale-cost-management-spec.md`第4节）已确认的方案：**索引本身分层拆分成"子类索引+索引的索引"，不引入向量检索**。

- 当本文件这一份表格本身也大到难以被"扫一眼"评估时，按分类维度（如按CWE大类、按语言/框架，具体分类维度留待实际条目积累后确定，本文件不预先杜撰分类维度）拆出`vuln-patterns/<category>/_index.md`子类索引，每份子类索引仍是同样的表格格式（第2节列定义不变）。
- 拆分后，本文件（`vuln-patterns/_index.md`）升级为"索引的索引"——只列每个子类索引的名称/条目数量概览/相对路径链接，不再直接列出单条知识条目。
- **语言覆盖度老实披露**（复用#13已确立原则）：按语言/框架拆分子类索引后，若某语言的条目数量明显偏少，消费方引用时必须显式披露"该语言当前只匹配到N条知识条目，完整性置信度较低"，不能装作所有语言深度一致。
- **中文文本匹配caveat**（复用#13已披露的LANG-04）：若"触发信号"涉及中文注释/字符串常量的文本匹配，标准按空格分词的正则匹配对中文不生效，需要单独处理；具体处理方式留待实际编写触发信号匹配逻辑时确定，本文件不预先假设。

## 8. 待办声明

分类粒度、条目文件具体命名规则、机械核对的具体实现，均留待未来实际编写知识条目/contracts层设计时确定，本文件不提前杜撰。

## 9. 生态映射引用批量状态说明（2026-08-14 如实登记）

本目录 148 个 vuln-pattern 条目文件中，含"生态映射引用"段落的共 104 个，且全部标注为"待创建"（无 1 个已填到具体 ECO 文件）。按任务口径约 169 个生态映射引用为待创建（逐行机械切分约 250+ 个引用短语，差异来自一行多引用与"等"后缀表述，本说明以约 169 计）。同口径下，`attack-patterns/` 43 个条目文件、`fix-patterns/` 22 个条目文件的"生态映射"段同样全部为"待创建"。

| 状态 | 数量 | 说明 |
|---|---|---|
| 已填（引用具体 ECO 文件） | 0 | 除 `_template.md` 示例外，无任何 vuln-pattern 条目的生态映射引用落到具体 `ecosystem-mappings/` 文件 |
| 待创建（vuln-patterns） | 约 169 | 104 个 vuln-pattern 条目文件的"生态映射引用"段全部为待创建 |
| 待创建（attack-patterns） | 43 | 43 个 attack-pattern 条目文件的"生态映射"段全部为待创建 |
| 待创建（fix-patterns） | 22 | 22 个 fix-pattern 条目文件的"生态映射"段全部为待创建 |

与现有 15 个 ECO 文件的关系：`ecosystem-mappings/` 现有 15 个 ECMAP 文件（ECMAP-PYTHON / ECMAP-PYTHON-DJANGO / ECMAP-PYTHON-FLASK / ECMAP-PYTHON-FASTAPI / ECMAP-JAVA / ECMAP-JAVA-SPRING / ECMAP-JAVASCRIPT / ECMAP-NODE-EXPRESS / ECMAP-PHP / ECMAP-PHP-LARAVEL / ECMAP-GO / ECMAP-CPP / ECMAP-RUST / ECMAP-CSHARP-DOTNET / ECMAP-RUBY-RAILS）是"语言/框架级"生态映射；而 vuln-pattern 条目中的"待创建"引用多为"模式×框架"级（如"Django CSRF 生态映射""C 危险函数生态映射"），粒度更细，不能与现有 15 个语言/框架级 ECO 文件一一对应。因此本批未把任何"待创建"引用更新为"已创建"——那样做会误把语言/框架级映射当成模式级映射。

长期计划：待建设生态映射按"模式×框架"粒度补齐——优先为 discoverable 条目补对应框架变体，再补齐其余；每新增一个模式级生态映射文件即在对应条目"生态映射引用"段更新为已创建。在补齐前，本索引与条目之间的生态映射引用状态以本节批量登记为准，禁止把"待创建"误述为已覆盖。
