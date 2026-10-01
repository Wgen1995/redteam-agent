# 攻击利用手法知识库索引维护规范（attack-patterns/）

`index_version: 2.1.0`
`declared_count: 120`
`count_source: index_rows`

> 来源：决策文档 `docs/research/decision/16-gensource-container-design-spec.md`（#16容器设计，已确认）第4节确定的存储形态；`docs/research/decision/24-category15-knowledge-organization-spec.md`（#15知识组织与检索，已确认）第4/5节索引结构/知识条目内部结构/强制显式查阅纪律/接口约束（明确#6为消费方）；`docs/research/decision/31-category13-language-stack-adaptation-spec.md`（#13语言/技术栈适配，已确认）第5节"适用语言/框架"字段要求；`docs/research/decision/25-category12-scale-cost-management-spec.md`（#12规模成本管理，已确认）第4节索引规模应对方案；`docs/research/decision/06-category-scoring-and-recommendations.md`（早期跨竞品打分框架，内容层面仍有效）F1/F2结论；`docs/research/decision/21-category06-exploit-proof-spec.md`（#6可利用性证明，已确认）关于利用形态与危害最小化的既有结论。本文件是上述决策规格落地到`knowledge/attack-patterns/`目录后的**索引维护规范**。

**状态声明（历史声明，现已过时——保留作沿革记录）**：本目录曾长期不含任何实际知识条目。2026-08-09，基于KBATCH-001种子知识迁移批次，首批4个攻击模式条目已落地（见第2节索引表），条目内容均有对应的vuln-pattern条目作为语义基础，不是编造内容。条目数量仍很少，覆盖面远未完整，未来仍需持续积累。

## 1. 这个目录解决什么问题（用途与消费方）

`attack-patterns/`收录**攻击利用手法知识**：给定一个已经在`vuln-patterns/`里有对应模式的漏洞，具体该怎么把"Source→Propagation→(未被Sanitizer拦下)→Sink"这条链，转化为一份能独立交给别人看懂、能重现的可利用性证明。这类知识关注的是**利用技术**本身（如"命令注入类可用猴子补丁式依赖模拟——把`os.system`替换为记录调用的`mock_system()`，在不真正对宿主机执行攻击者命令的前提下证明危险调用确实被触发"，参见`skills/exploit-proof/SKILL.md`步骤C.4已提及的可选方法），不是漏洞判定本身，也不是修复方案。

**消费方**：`skills/exploit-proof/SKILL.md`（#6可利用性证明）。#24（#15知识组织规格）第5节接口约束原文已明确列出"消费方：#3（vuln-patterns）、#6（attack-patterns）、#7（fix-patterns）"，本目录的消费关系直接依据该条款确定。#6在判断某候选该用哪种具体利用手法打包既有证据时（尤其命令注入/危险文件写入等可选择依赖模拟方法的类别），应先查本目录是否已有现成的可复用手法条目，而不是每次临时现想。

**不服务的场景**：#6是否达到触发范围（`verification_verdict`=已确认且置信度过阈值）的判断，仍由#4/#6自己的逻辑决定，不查本目录；本目录不收录"什么代码信号意味着有漏洞"（那是`vuln-patterns/`）或修复方案（那是`fix-patterns/`）。

## 2. 索引表格格式规范

索引是"扫一眼就知道该不该细看"的轻量表格，不是按字母顺序随便列的清单。列定义：

| 列名 | 含义 |
|---|---|
| 条目ID | 唯一标识，指向`attack-patterns/`下对应的条目文件（文件命名规则见第3节） |
| 触发信号 | 什么信号出现时该查这条——典型是"命中的vuln-pattern条目ID + 目标语言/运行环境特征"的组合（如"命中`vuln-patterns/`某SQL注入条目 + 目标语言支持数据库驱动的良性标记读取"），不是模糊的攻击类型名称 |
| 适用语言/框架 | 本条目适用的语言/框架范围（#13已确认要求新增此列）。利用手法的语言相关性通常比漏洞模式更强（如猴子补丁式依赖模拟在动态语言天然好用，静态编译语言是另一套做法，#13已确立此结论），支持按#1/#2产出的语言/框架事实过滤 |
| 一句话摘要 | 一句话说明这条利用手法演示的是什么、用什么方式演示 |
| 交叉引用 | 建立在哪个`vuln-patterns/`条目之上（#15已确认的交叉引用要求原文："attack-pattern条目应指向建立在哪个vuln-pattern之上"），供#6/#4溯源该利用手法证明的是哪个漏洞模式 |

**当前索引表（120条）**。计数以本文件唯一`ATK-*`数据行为准，覆盖目录内全部正式条目文件：

| 条目ID | 触发信号 | 适用语言/框架 | 一句话摘要 | 交叉引用（建立在哪个vuln-pattern条目之上） |
|---|---|---|---|---|
| ATK-SQLI-BENIGN-01（`sql-injection-benign-marker.md`） | 命中`VULN-SQLI-STRCONCAT-01` + 目标支持数据库驱动的良性标记读取 | 所有DB-API风格驱动（Python/PHP/Java/Node等） | 良性差分查询证明SQL注入——用良性标记值不整库拖库 | VULN-SQLI-STRCONCAT-01 |
| ATK-XSS-BENIGN-DOM-01（`xss-benign-dom-marker.md`） | 命中`VULN-XSS-AUTOESCAPE-01`或`VULN-XSS-RAWOUTPUT-01` + 目标有HTTP响应输出 | Jinja2/Django/Twig/原生PHP等有HTML输出的场景 | 无害标记DOM/响应上下文证明XSS——注入良性标记而非恶意脚本 | VULN-XSS-AUTOESCAPE-01, VULN-XSS-RAWOUTPUT-01 |
| ATK-CRYPTO-OFFLINE-COST-01（`weak-hash-offline-cost.md`） | 命中`VULN-CRYPTO-WEAKHASH-01` + 哈希值可离线获取 | 不限语言，密码存储逻辑处均适用 | 离线参数与成本证明——不使用真实凭证，仅证明弱哈希可被快速计算 | VULN-CRYPTO-WEAKHASH-01 |
| ATK-AUTHZ-DUAL-IDENTITY-01（`missing-authz-dual-identity.md`） | 命中`VULN-AUTHZ-MISSING-01` + 目标有多身份/多租户能力 | 所有有装饰器/中间件式授权机制的Web框架 | 双身份/双租户对照证明缺失授权——低权限身份能访问高权限资源 | VULN-AUTHZ-MISSING-01 |
| ATK-INJ-SPECELEM-01（`inj-special-element-benign-marker.md`） **[Inferred]** | 命中`VULN-INJ-SPECELEM-01` + 目标解释器可观察执行结果 | 不限语言/框架（日志/CSV/EL/模板引擎场景） | 良性标记证明特殊元素注入——日志伪造/CSV公式/EL求值/模板渲染 | VULN-INJ-SPECELEM-01 |
| ATK-INJ-CMD-01（`inj-command-benign-marker.md`） | 命中`VULN-INJ-CMD-01` + 目标支持命令执行副作用观察 | Python/PHP/Java/Node.js/Go/Ruby等所有执行shell命令的语言 | 良性标记命令分隔符注入证明——用echo+良性标记而非破坏性命令 | VULN-INJ-CMD-01 |
| ATK-INJ-RESOURCE-01（`inj-resource-benign-probe.md`） | 命中`VULN-INJ-RESOURCE-01` + 目标可观察资源访问结果 | Python/PHP/Java/Node.js/Go等所有将外部输入用作资源标识符的语言 | 良性资源标识符探测证明——读/etc/hostname而非敏感文件 | VULN-INJ-RESOURCE-01 |
| ATK-INJ-CRLF-01（`inj-crlf-benign-header.md`） **[Inferred]** | 命中`VULN-INJ-CRLF-01` + 目标框架未内置CRLF过滤 | Python/Java/PHP/Node.js等所有构造行结构数据的语言 | 良性标记CRLF头注入证明——用X-GenSource-Marker头而非恶意Set-Cookie | VULN-INJ-CRLF-01 |
| ATK-INJ-CODE-01（`inj-code-benign-eval.md`） | 命中`VULN-INJ-CODE-01` + 目标支持动态代码执行结果观察 | Python/PHP/JavaScript/Java/Ruby等所有支持动态代码执行的语言 | 良性标记表达式求值证明代码注入——用1+1或环境变量读取而非RCE | VULN-INJ-CODE-01 |
| ATK-INJ-FMTSTR-01（`inj-format-string-benign-specifier.md`） **[Inferred]** | 命中`VULN-INJ-FMTSTR-01` + 目标可观察格式化输出结果 | C/C++/PHP等使用格式化字符串机制的语言 | 良性格式化说明符证明格式化字符串注入——用%x读取而非%n写入 | VULN-INJ-FMTSTR-01 |
| ATK-INJ-XXE-01（`inj-xxe-benign-entity.md`） **[Inferred]** | 命中`VULN-INJ-XXE-01` + 目标XML解析器可观察解析结果 | Java/Python(lxml)/PHP/.NET等所有解析XML的语言 | 良性外部实体文件读取证明XXE——读/etc/hostname而非敏感文件 | VULN-INJ-XXE-01 |
| ATK-INJ-SSRF-01（`inj-ssrf-benign-callback.md`） | 命中`VULN-INJ-SSRF-01` + 目标可观察网络请求结果 | Python/Java/Node.js/PHP/Go等所有支持HTTP客户端库的语言 | 良性回调URL探测证明SSRF——用127.0.0.1探测而非窃取云凭证 | VULN-INJ-SSRF-01 |
| ATK-INJ-DESERIAL-01（`inj-deserialization-benign-gadget.md`） | 命中`VULN-INJ-DESERIAL-01` + 目标可观察反序列化副作用 | Python/Java/PHP/.NET/Ruby等所有支持原生对象序列化的语言 | 良性gadget链证明反序列化注入——用环境变量读取而非RCE | VULN-INJ-DESERIAL-01 |
| ATK-HW-MEMPROT-01（`hw-memory-protection-benign-probe.md`） **[Proposed]** | 命中`VULN-HW-MEMPROT-01` + 可检查内存保护配置 | C/嵌入式固件/MMU/MPU | 硬件内存保护良性探测——检查W^X/范围隔离/镜像校验配置 | VULN-HW-MEMPROT-01 |
| ATK-HW-DEBUG-01（`hw-debug-interface-benign-probe.md`） **[Proposed]** | 命中`VULN-HW-DEBUG-01` + 可物理接触调试接口 | IoT/嵌入式设备/SoC安全 | 调试接口良性探测——检查JTAG/SWD可用性 | VULN-HW-DEBUG-01 |
| ATK-HW-FIRMWARE-01（`hw-firmware-update-benign-probe.md`） **[Proposed]** | 命中`VULN-HW-FIRMWARE-01` + 可检查固件更新能力 | IoT/嵌入式设备/SoC安全 | 固件更新能力良性探测——检查更新接口/签名验证 | VULN-HW-FIRMWARE-01 |
| ATK-HW-ROOT-01（`hw-root-of-trust-benign-probe.md`） **[Proposed]** | 命中`VULN-HW-ROOT-01` + 可检查信任根存储配置 | C/嵌入式固件/eFuse/ROM | 信任根不可变性良性探测——检查存储位置/写入保护 | VULN-HW-ROOT-01 |
| ATK-HW-LOGIC-01（`hw-logic-fault-benign-probe.md`） **[Inferred]** | 命中`VULN-HW-LOGIC-01` + 可检查RTL/固件FSM设计 | Verilog/VHDL/SoC设计 | 硬件逻辑故障良性探测——检查FSM错误处理/通道同步 | VULN-HW-LOGIC-01 |
| ATK-HW-FABRIC-01（`hw-fabric-security-benign-probe.md`） **[Proposed]** | 命中`VULN-HW-FABRIC-01` + 可检查总线安全配置 | Verilog/VHDL/SoC/AXI | 片上总线安全良性探测——检查安全位/写保护配置 | VULN-HW-FABRIC-01 |
| ATK-HW-RE-01（`hw-reverse-engineering-benign-probe.md`） **[Proposed]** | 命中`VULN-HW-RE-01` + 可检查芯片物理防护 | IC设计/SoC安全 | 逆向工程防护良性探测——检查金属层遮挡/走线屏蔽 | VULN-HW-RE-01 |
| ATK-CODE-DANGEROUS-01（`code-dangerous-function-benign-probe.md`） **[Proposed]** | 命中`VULN-CODE-DANGEROUS-01` + 可观察危险函数执行结果 | C/C++/通用 | 危险函数良性探测——超长输入触发溢出/崩溃 | VULN-CODE-DANGEROUS-01 |
| ATK-CODE-DYNCTRL-01（`code-dynamic-control-benign-probe.md`） **[Proposed]** | 命中`VULN-CODE-DYNCTRL-01` + 可观察动态加载结果 | Python/Java/Node.js | 动态代码控制良性探测——加载良性标准库模块证明无白名单 | VULN-CODE-DYNCTRL-01 |
| ATK-CODE-EMBEDDED-01（`code-embedded-malicious-benign-probe.md`） **[Proposed]** | 命中`VULN-CODE-EMBEDDED-01` + 可检查包来源/行为 | npm/PyPI/通用供应链 | 嵌入式恶意代码良性探测——检查包来源/安装脚本/运行时行为 | VULN-CODE-EMBEDDED-01 |
| ATK-CODE-HIDDEN-01（`code-hidden-functionality-benign-probe.md`） **[Proposed]** | 命中`VULN-CODE-HIDDEN-01` + 可检查隐藏功能触发条件 | Web/桌面/移动/通用 | 隐藏功能良性探测——用debug_mode参数触发隐藏功能 | VULN-CODE-HIDDEN-01 |
| ATK-CODE-PROHIBITED-01（`code-prohibited-usage-benign-probe.md`） **[Proposed]** | 命中`VULN-CODE-PROHIBITED-01` + 可运行linter检查 | C/C++/Java/通用linter | 禁用代码良性探测——linter检测禁用API且无CI门控 | VULN-CODE-PROHIBITED-01 |
| ATK-CODE-SPECMISMATCH-01（`code-spec-mismatch-benign-probe.md`） **[Inferred]** | 命中`VULN-CODE-SPECMISMATCH-01` + 有规范文档 | 不限语言/框架 | 规范不匹配良性探测——规范比对发现安全检查被简化/遗漏 | VULN-CODE-SPECMISMATCH-01 |
| ATK-CODE-UNDEF-01（`code-undefined-behavior-benign-probe.md`） **[Inferred]** | 命中`VULN-CODE-UNDEF-01` + 可编译/运行代码 | C/C++/Rust/通用编译器 | 未定义行为良性探测——UBSan检测/优化级别比对 | VULN-CODE-UNDEF-01 |
| ATK-AI-PROMPTINJ-01（`ai-prompt-injection-benign-marker.md`） **[Proposed]** | 命中`VULN-AI-PROMPTINJ-01` + 可向LLM提供输入 | LLM应用(OpenAI/Anthropic) | 提示注入良性标记——用"回复GENSOURCE_INJECTED"测试指令覆盖 | VULN-AI-PROMPTINJ-01 |
| ATK-AI-ADVERSARIAL-01（`ai-adversarial-input-benign-marker.md`） **[Inferred]** | 命中`VULN-AI-ADVERSARIAL-01` + 可向AI/ML系统提供输入 | ML框架/识别系统 | 对抗性输入良性标记——良性对抗性样本测试模型是否被误导 | VULN-AI-ADVERSARIAL-01 |
| ATK-AI-CONFIG-01（`ai-insecure-config-benign-probe.md`） **[Proposed]** | 命中`VULN-AI-CONFIG-01` + 可检查推理参数配置 | LLM应用(OpenAI/Anthropic API) | 推理参数不安全配置良性探测——检查温度/top_p配置 | VULN-AI-CONFIG-01 |
| ATK-AI-OUTPUT-01（`ai-output-validation-benign-marker.md`） **[Proposed]** | 命中`VULN-AI-OUTPUT-01` + 可操纵AI输出 | LLM应用/代码生成 | AI输出验证失效良性标记——AI输出含GENSOURCE_MARKER进入下游 | VULN-AI-OUTPUT-01 |
| ATK-AI-OPTIMIZATION-01（`ai-insecure-optimization-benign-probe.md`） **[Inferred]** | 命中`VULN-AI-OPTIMIZATION-01` + 可编译/运行代码 | C/C++编译器/AI模型优化 | 不安全优化良性探测——-O0 vs -O2安全代码行为比对 | VULN-AI-OPTIMIZATION-01 |
| ATK-SPHERE-ISOLATION-01（`sphere-isolation-benign-cross.md`） **[Proposed]** | 命中`VULN-SPHERE-ISOLATION-01` + 有多租户/多进程能力 | SaaS/容器/Unix | 隔离失效良性跨域——双租户对照测试A能否访问B数据 | VULN-SPHERE-ISOLATION-01 |
| ATK-SPHERE-ALTPATH-01（`sphere-alternate-path-benign-probe.md`） **[Proposed]** | 命中`VULN-SPHERE-ALTPATH-01` + 存在替代路径 | Web/微服务/通用 | 替代路径良性探测——通过无认证替代路径请求资源 | VULN-SPHERE-ALTPATH-01 |
| ATK-SPHERE-CHANNEL-01（`sphere-channel-benign-probe.md`） **[Proposed]** | 命中`VULN-SPHERE-CHANNEL-01` + 可在网络中间位置观察 | 不限语言/HTTP/socket | 信道保护良性探测——抓包观察通信是否为明文 | VULN-SPHERE-CHANNEL-01 |
| ATK-SPHERE-EXTINFLUENCE-01（`sphere-external-influence-benign-probe.md`） **[Proposed]** | 命中`VULN-SPHERE-EXTINFLUENCE-01` + 可向域定义接口提供输入 | K8s/云服务/Web配置 | 域定义外部影响良性探测——低权限用户尝试修改信任域 | VULN-SPHERE-EXTINFLUENCE-01 |
| ATK-SPHERE-EXTREF-01（`sphere-external-reference-benign-probe.md`） **[Proposed]** | 命中`VULN-SPHERE-EXTREF-01` + 可控制URL/引用参数 | Web/API/OAuth | 跨域引用良性探测——用127.0.0.1测试系统是否向非预期域请求 | VULN-SPHERE-EXTREF-01 |
| ATK-SPHERE-TRANSFER-01（`sphere-incorrect-transfer-benign-probe.md`） **[Proposed]** | 命中`VULN-SPHERE-TRANSFER-01` + 可观察跨域响应内容 | 微服务/API Gateway | 域间转移良性探测——观察API响应是否包含不应转移的内部数据 | VULN-SPHERE-TRANSFER-01 |
| ATK-SPHERE-EXPOSURE-01（`sphere-wrong-exposure-benign-probe.md`） **[Proposed]** | 命中`VULN-SPHERE-EXPOSURE-01` + 可从错误域访问资源 | Web/K8s/云服务 | 资源暴露良性探测——从公网访问管理接口确认可达 | VULN-SPHERE-EXPOSURE-01 |
| ATK-UI-MISREP-01（`ui-misrepresentation-benign-probe.md`） **[Proposed]** | 命中`VULN-UI-MISREP-01` + 可检查UI显示与实际值 | 浏览器/邮件/Web/移动 | UI误表示良性探测——比对显示文本与href是否一致 | VULN-UI-MISREP-01 |
| ATK-UI-WARNING-01（`ui-insufficient-warning-benign-probe.md`） **[Proposed]** | 命中`VULN-UI-WARNING-01` + 可执行危险操作测试 | Web/桌面/移动 | UI警告不足良性探测——尝试执行危险操作观察是否有警告 | VULN-UI-WARNING-01 |
| ATK-UI-DISCREPANCY-01（`ui-security-discrepancy-benign-probe.md`） **[Proposed]** | 命中`VULN-UI-DISCREPANCY-01` + 可检查安全状态显示与实际行为 | Web/移动/桌面 | 安全功能UI差异良性探测——比对安全状态显示与实际行为 | VULN-UI-DISCREPANCY-01 |
| ATK-INTER-CONFUSED-01（`inter-confused-deputy-benign-probe.md`） **[Proposed]** | 命中`VULN-INTER-CONFUSED-01` + 可向代理程序发送请求 | 编译器/API Gateway/系统服务 | 混淆代理人良性探测——低权限用户请求代理写入良性测试文件 | VULN-INTER-CONFUSED-01 |
| ATK-INTER-INTERPCONFLICT-01（`inter-interpretation-conflict-benign-probe.md`） **[Proposed]** | 命中`VULN-INTER-INTERPCONFLICT-01` + 可向跨实体接口提供输入 | URL解析/编码/HTTP请求解析 | 解释冲突良性探测——歧义输入测试不同实体解释是否一致 | VULN-INTER-INTERPCONFLICT-01 |
| ATK-INTER-SPECVIOLATION-01（`inter-spec-violation-benign-probe.md`） **[Proposed]** | 命中`VULN-INTER-SPECVIOLATION-01` + 有明确接口规范 | C/Rust/通用API/库接口 | 调用方违反规范良性探测——违反规范的调用测试被调用方是否检查 | VULN-INTER-SPECVIOLATION-01 |
| ATK-SUPPLY-UNTRUSTWORTHY-01（`supply-untrustworthy-benign-probe.md`） **[Proposed]** | 命中`VULN-SUPPLY-UNTRUSTWORTHY-01` + 可检查包来源 | npm/PyPI/通用包管理 | 不可信组件良性探测——检查包verified publisher/provenance/签名 | VULN-SUPPLY-UNTRUSTWORTHY-01 |
| ATK-SUPPLY-VULNDEP-01（`supply-vulnerable-dep-version-check.md`） **[Proposed]** | 命中`VULN-SUPPLY-VULNDEP-01` + 可运行SCA扫描 | npm/PyPI/通用SCA | 易受攻击依赖版本检测——SCA扫描依赖版本是否匹配已知CVE | VULN-SUPPLY-VULNDEP-01 |
| ATK-STATE-EXTCONTROL-01（`state-external-control-benign-probe.md`） **[Proposed]** | 命中`VULN-STATE-EXTCONTROL-01` + 可向状态接口提供输入 | Web(mass assignment)/API | 状态外部控制良性探测——请求含role=viewer测试是否能修改关键状态 | VULN-STATE-EXTCONTROL-01 |
| ATK-STATE-INCOMPLETE-01（`state-incomplete-distinction-benign-probe.md`） **[Proposed]** | 命中`VULN-STATE-INCOMPLETE-01` + 可达到中间状态 | 状态机/认证框架 | 状态区分不完整良性探测——中间状态访问需要完全认证的资源 | VULN-STATE-INCOMPLETE-01 |
| ATK-PHYSICAL-ENV-01（`physical-environment-benign-probe.md`） **[Inferred]** | 命中`VULN-PHYSICAL-ENV-01` + 可检查环境监测配置 | 硬件安全/IoT/嵌入式 | 环境条件良性探测——检查环境监测配置缺失 | VULN-PHYSICAL-ENV-01 |
| ATK-PHYSICAL-POWER-01（`physical-power-benign-probe.md`） **[Inferred]** | 命中`VULN-PHYSICAL-POWER-01` + 可检查密码操作实现 | 嵌入式/智能卡/硬件密码 | 功耗侧信道良性探测——检查密码操作是否依赖密钥位条件分支 | VULN-PHYSICAL-POWER-01 |
| ATK-TYPE-CAST-01（`type-incorrect-cast-benign-probe.md`） **[Proposed]** | 命中`VULN-TYPE-CAST-01` + 可提供触发转换错误的输入 | C/C++/Rust/Java/通用类型转换 | 类型转换错误良性探测——-1触发有符号到无符号转换变为UINT_MAX | VULN-TYPE-CAST-01 |
| ATK-NAME-RESOLUTION-01（`name-incorrect-resolution-benign-probe.md`） **[Proposed]** | 命中`VULN-NAME-RESOLUTION-01` + 可控制名称解析路径 | Python(模块搜索)/DNS/通用 | 名称解析错误良性探测——sys.path劫持使良性模块优先加载 | VULN-NAME-RESOLUTION-01 |
| ATK-PROCESS-CONTROL-01（`process-control-benign-probe.md`） **[Proposed]** | 命中`VULN-PROCESS-CONTROL-01` + 可控制进程执行内容 | OS/容器/通用进程管理 | 进程控制良性探测——良性测试代码触发进程执行 | VULN-PROCESS-CONTROL-01 |
| ATK-ENCAP-INSUFFICIENT-01（`encapsulation-benign-probe.md`） **[Proposed]** | 命中`VULN-ENCAP-INSUFFICIENT-01` + 可访问类/模块接口 | Java/C++/Python/通用OOP | 封装不足良性探测——直接修改public字段/可变对象 | VULN-ENCAP-INSUFFICIENT-01 |
| ATK-ENC-ENCODING-01（`encoding-benign-marker.md`） **[Proposed]** | 命中`VULN-ENC-ENCODING-01` + 可控制输出数据 | Python(Jinja2)/Java/通用模板 | 输出编码失效良性标记——alert('GENSOURCE_ENC')测试输出是否被编码 | VULN-ENC-ENCODING-01 |
| ATK-CONC-RACE-01（`conc-race-toctou-benign.md`） **[Proposed]** | 命中`VULN-CONC-RACE-01` + 共享资源可被并发修改 | Python/Java/Go/C/C++/Node.js等所有支持并发的语言 | TOCTOU竞态条件良性证明——并发请求证明检查-使用窗口存在 | VULN-CONC-RACE-01 |
| ATK-CONC-LOCKING-01（`conc-locking-deadlock-benign.md`） **[Proposed]** | 命中`VULN-CONC-LOCKING-01` + 锁未释放/死锁可通过并发请求触发 | Python/Java/C++/Go/C等所有提供锁机制的语言 | 锁使用不当死锁良性证明——触发异常路径使锁未释放后确认请求被阻塞 | VULN-CONC-LOCKING-01 |
| ATK-EXC-UNCHECKED-01（`exc-unchecked-error-path-benign.md`） **[Proposed]** | 命中`VULN-EXC-UNCHECKED-01` + 能构造使函数失败的输入 | C/C++/Go/Python/Java等所有有可失败函数调用的语言 | 未检查错误路径良性证明——构造使验证函数失败的输入确认仍通过 | VULN-EXC-UNCHECKED-01 |
| ATK-EXC-SWALLOWED-01（`exc-swallowed-exception-benign.md`） **[Proposed]** | 命中`VULN-EXC-SWALLOWED-01` + 能构造使安全检查抛异常的输入 | Python/Java/JavaScript/C#/PHP等所有有异常处理的语言 | 异常吞没安全绕过良性证明——构造使安全检查抛异常的输入确认仍通过 | VULN-EXC-SWALLOWED-01 |
| ATK-EXC-FAILOPEN-01（`exc-failopen-benign.md`） **[Proposed]** | 命中`VULN-EXC-FAILOPEN-01` + 能触发安全检查失败 | 不限语言/框架，任何有安全检查逻辑的代码 | fail-open安全绕过良性证明——触发安全检查失败确认仍通过 | VULN-EXC-FAILOPEN-01 |
| ATK-CALC-INTOVERFLOW-01（`calc-integer-overflow-benign.md`） **[Proposed]** | 命中`VULN-CALC-INTOVERFLOW-01` + 能提供大数值触发溢出 | C/C++/Java/Go/Python等所有有数值计算的语言 | 整数溢出良性证明——提供大数值确认计算结果回绕 | VULN-CALC-INTOVERFLOW-01 |
| ATK-CALC-COMPARE-01（`calc-comparison-bypass-benign.md`) **[Proposed]** | 命中`VULN-CALC-COMPARE-01` + 能构造使错误比较产生偏差的输入 | Java/C/C++/JavaScript/PHP等所有有比较操作的语言 | 比较错误绕过良性证明——构造使错误比较产生偏差的输入 | VULN-CALC-COMPARE-01 |
| ATK-CALC-INCOMPLETE-01（`calc-incomplete-comparison-benign.md`） **[Proposed]** | 命中`VULN-CALC-INCOMPLETE-01` + 能构造满足部分比较因子的输入 | 不限语言/框架，密码比较/令牌验证/权限检查场景 | 不完整比较绕过良性证明——构造满足部分因子的输入确认通过 | VULN-CALC-INCOMPLETE-01 |
| ATK-CALC-LENGTH-01（`calc-length-mismatch-benign.md`） **[Proposed]** | 命中`VULN-CALC-LENGTH-01` + 能发送带长度参数的数据 | C/C++/Python(ctypes)/Go/Rust(unsafe)等所有有缓冲区操作的语言 | 长度参数不匹配良性证明——构造长度不匹配的数据包确认越界访问 | VULN-CALC-LENGTH-01 |
| ATK-PROT-CLIENTSIDE-01（`prot-clientside-bypass-benign.md`） **[Proposed]** | 命中`VULN-PROT-CLIENTSIDE-01` + 能绕过客户端控制直接访问服务端 | Web前端(JS)/移动App/Electron，服务端框架 | 客户端控制绕过良性证明——直接发送API请求绕过客户端验证 | VULN-PROT-CLIENTSIDE-01 |
| ATK-PROT-OBSCURITY-01（`prot-obscurity-discover-benign.md`） **[Proposed]** | 命中`VULN-PROT-OBSCURITY-01` + 隐蔽信息可被合理途径发现 | 不限语言/框架，隐藏URL/自定义算法场景 | 隐蔽性发现良性证明——URL枚举/信息泄露发现隐藏URL后直接访问 | VULN-PROT-OBSCURITY-01 |
| ATK-PROT-SINGLEFACTOR-01（`prot-singlefactor-bypass-benign.md`） **[Proposed]** | 命中`VULN-PROT-SINGLEFACTOR-01` + 能获取单一因素 | 不限语言/框架，认证/特权操作场景 | 单因素绕过良性证明——使用单一因素确认无需第二因素即可认证 | VULN-PROT-SINGLEFACTOR-01 |
| ATK-PROT-GUESSABLE-01（`prot-guessable-captcha-benign.md`） **[Proposed]** | 命中`VULN-PROT-GUESSABLE-01` + 挑战可被自动化求解 | Web应用(自定义CAPTCHA)、移动应用、API | 可猜测CAPTCHA自动化求解良性证明——自动化程序尝试通过挑战统计通过率 | VULN-PROT-GUESSABLE-01 |
| ATK-CRYPTO-CLEARTEXT-01（`cleartext-capture-benign.md`） **[Inferred]** | 命中`VULN-CRYPTO-NOENCRYPT-01` + 敏感数据走明文通道或明文存储 | 不限语言，传输侧(网络嗅探)与存储侧(存储读取)均适用 | 明文通道被动截获良性证明——用良性测试凭证证明截获能力 | VULN-CRYPTO-NOENCRYPT-01 |
| ATK-CRYPTO-KEYSIZE-01（`weak-key-cost-benign.md`） **[Inferred]** | 命中`VULN-CRYPTO-WEAKSTRENGTH-01` + 公钥/密文/哈希值可离线获取 | 不限语言，离线计算环境 | 短密钥/低迭代破解成本证明——用测试密钥证明破解耗时远低于基线 | VULN-CRYPTO-WEAKSTRENGTH-01 |
| ATK-CRYPTO-RNGPREDICT-01（`weak-rng-prediction-benign.md`） **[Inferred]** | 命中`VULN-CRYPTO-WEAKRNG-01` + 安全场景使用非CSPRNG或可预测种子 | Python(random)/Java(Random)/Node(Math.random)/Go(math/rand)等弱RNG场景 | 弱RNG预测良性证明——用测试随机值证明输出可预测/可重现 | VULN-CRYPTO-WEAKRNG-01 |
| ATK-CRYPTO-FORGEDDATA-01（`forged-data-benign-marker.md`） **[Inferred]** | 命中`VULN-CRYPTO-NOAUTHVERIFY-01` + 外部数据未验证签名/证书/完整性 | 不限语言，中间人代理或可控数据源场景 | 伪造/篡改外部数据良性标记证明——用良性标记替换数据证明未验证真实性 | VULN-CRYPTO-NOAUTHVERIFY-01 |
| ATK-CRYPTO-CSRF-01（`csrf-benign-marker.md`） **[Inferred]** | 命中`VULN-CRYPTO-NOORIGIN-01` + 状态变更操作无CSRF token/Origin校验 | Django/Flask/Express/Spring等Web框架及WebSocket场景 | CSRF跨域状态变更良性标记证明——用良性标记构造跨域请求证明被接受 | VULN-CRYPTO-NOORIGIN-01 |
| ATK-CRYPTO-NONCEREUSE-01（`nonce-reuse-benign.md`） **[Inferred]** | 命中`VULN-CRYPTO-KEYLIFE-01` + nonce/IV在同一密钥下重复使用(CTR/GCM) | Python(cryptography)/Java(JCA)/Node(crypto)/Go(cipher)等加密场景 | nonce重用明文泄露良性证明——用测试明文证明异或可还原明文关系 | VULN-CRYPTO-KEYLIFE-01 |
| ATK-CRYPTO-TAMPER-01（`tamper-ciphertext-benign.md`） **[Inferred]** | 命中`VULN-CRYPTO-MISSINGSTEP-01` + 加密未伴随认证(CBC/CTR无MAC) | Python(cryptography)/Java(JCA)/Node(crypto)/Go(cipher)等加密场景 | 密文篡改/认证缺失良性标记证明——用良性标记篡改密文证明未检测篡改 | VULN-CRYPTO-MISSINGSTEP-01 |
| ATK-MEM-BOUNDS-01（`mem-bounds-benign-overflow.md`） **[Inferred]** | 命中`VULN-MEM-BOUNDS-01` + 目标可编译运行或可使用ASan | C/C++/Rust(unsafe)等可使用ASan的环境 | 良性越界标记证明缓冲区边界失效——用ASan报告而非实际代码执行 | VULN-MEM-BOUNDS-01 |
| ATK-MEM-INDEX-01（`mem-index-benign-oob.md`） **[Inferred]** | 命中`VULN-MEM-INDEX-01` + 目标可运行或可使用ASan | C/C++/Rust(unsafe)等可使用ASan的环境 | 良性越界索引读取证明索引验证缺失——用ASan报告而非越界写入 | VULN-MEM-INDEX-01 |
| ATK-MEM-LAYOUT-01（`mem-layout-benign-diff.md`） **[Inferred]** | 命中`VULN-MEM-LAYOUT-01` + 可验证跨平台行为差异 | C/C++(结构体memcpy)跨平台场景 | 跨平台布局差异证明布局依赖——不同字节序产生不同解析结果 | VULN-MEM-LAYOUT-01 |
| ATK-MEM-NULLTERM-01（`mem-nullterm-benign-overread.md`） **[Inferred]** | 命中`VULN-MEM-NULLTERM-01` + 目标可运行或可使用ASan | C(strncpy陷阱)/C++(char*操作) | 良性过读标记证明空终止符缺失——用ASan报告而非泄露大量数据 | VULN-MEM-NULLTERM-01 |
| ATK-MEM-PTR-01（`mem-ptr-benign-null.md`） **[Inferred]** | 命中`VULN-MEM-PTR-01` + 可通过IOCTL/接口传入指针值 | C/C++(kernel IOCTL)/系统编程 | 良性指针值注入证明不可信指针解引用——用NULL触发安全失败而非任意地址写入 | VULN-MEM-PTR-01 |
| ATK-FILE-TRAVERSAL-01（`file-traversal-benign-read.md`） **[Inferred]** | 命中`VULN-FILE-TRAVERSAL-01` + 目标可观察文件读取结果 | 所有将外部输入用作文件路径的语言 | 良性遍历标记文件读取证明路径遍历——读/etc/hostname而非敏感文件 | VULN-FILE-TRAVERSAL-01 |
| ATK-FILE-SYMLINK-01（`file-symlink-benign-redirect.md`） **[Inferred]** | 命中`VULN-FILE-SYMLINK-01` + 可创建symlink+可观察文件操作结果 | Unix文件系统/C/Python/Java/Go | 良性symlink重定向证明链接跟随——指向良性标记文件而非敏感文件 | VULN-FILE-SYMLINK-01 |
| ATK-FILE-PATHEQUIV-01（`file-pathequiv-benign-variant.md`） **[Inferred]** | 命中`VULN-FILE-PATHEQUIV-01` + 目标可观察文件访问结果 | Windows(大小写/末尾点)/Unix(多重斜杠) | 良性等价路径标记证明路径等价绕过——使用等价路径访问良性标记文件 | VULN-FILE-PATHEQUIV-01 |
| ATK-FILE-VIRTUAL-01（`file-virtual-benign-probe.md`） **[Inferred]** | 命中`VULN-FILE-VIRTUAL-01` + 目标可观察文件操作行为 | Windows(CON/NUL)/Linux(/dev/) | 良性虚拟资源名探测证明设备名处理——用NUL/dev/null而非/dev/random | VULN-FILE-VIRTUAL-01 |
| ATK-FILE-SEARCHPATH-01（`file-searchpath-benign-implant.md`） **[Inferred]** | 命中`VULN-FILE-SEARCHPATH-01` + 可对搜索路径目录写入+可观察加载结果 | C/C++/Python/Java/Go/Rust等所有加载外部代码/库的语言 | 良性搜索路径植入证明不可信搜索路径——植入良性标记脚本而非恶意代码 | VULN-FILE-SEARCHPATH-01 |
| ATK-FILE-TEMPFILE-01（`file-tempfile-benign-predict.md`） **[Inferred]** | 命中`VULN-FILE-TEMPFILE-01` + 临时文件名可预测+可对临时目录写入 | C/Python/Java/Go/Rust等所有创建临时文件的语言 | 良性临时文件预测证明不安全临时文件——创建良性标记文件而非指向敏感文件的symlink | VULN-FILE-TEMPFILE-01 |
| ATK-INPUT-XML-01（`input-xml-benign-entity.md`） **[Inferred]** | 命中`VULN-INPUT-XML-01` + 目标可观察XML解析结果 | Java/Python/PHP/.NET等所有解析XML的语言 | 良性外部实体文件读取证明XML验证缺失——读/etc/hostname而非敏感文件 | VULN-INPUT-XML-01 |
| ATK-INPUT-MISPARSE-01（`input-misparse-benign-double-encode.md`） **[Inferred]** | 命中`VULN-INPUT-MISPARSE-01` + 有多层解析+可观察解析结果 | Web代理/服务器/API网关 | 良性双重编码标记证明解析差异绕过——双重编码遍历读/etc/hostname | VULN-INPUT-MISPARSE-01 |
| ATK-INPUT-SPECELEM-01（`input-specelem-benign-structure.md`） **[Inferred]** | 命中`VULN-INPUT-SPECELEM-01` + 可观察解析结果/异常行为 | 不限语言/框架(CSV/JSON/协议解析) | 良性结构异常输入证明特殊元素处理错误——缺失分隔符观察异常行为 | VULN-INPUT-SPECELEM-01 |
| ATK-INPUT-CASE-01（`input-case-benign-variant.md`） **[Inferred]** | 命中`VULN-INPUT-CASE-01` + 目标可观察检查/操作结果 | Windows文件系统/数据库COLLATION/HTTP | 良性大小写变体标记证明大小写绕过——使用大小写变体访问良性标记文件 | VULN-INPUT-CASE-01 |
| ATK-INPUT-COLLAPSE-01（`input-collapse-benign-composed.md`） **[Inferred]** | 命中`VULN-INPUT-COLLAPSE-01` + 有Unicode规范化+可观察验证结果 | Python(unicodedata)/Java(Normalizer)/数据库 | 良性组合字符变体标记证明坍缩绕过——组合字符规范化后坍缩为黑名单值 | VULN-INPUT-COLLAPSE-01 |
| ATK-INPUT-HANDLING-01（`input-handling-benign-unexpected.md`） **[Inferred]** | 命中`VULN-INPUT-HANDLING-01` + 可观察处理结果/异常 | 动态语言(Python/JS)更易出现 | 良性非预期类型输入证明处理不当——传入None/整数观察异常行为 | VULN-INPUT-HANDLING-01 |
| ATK-INPUT-REGEX-01（`input-regex-benign-redos.md`） **[Inferred]** | 命中`VULN-INPUT-REGEX-01` + 可观察验证结果/响应时间 | Python(re)/Java(regex)/JS(RegExp)/PHP(PCRE)等回溯引擎 | 良性宽松匹配/ReDoS标记证明正则错误——空字符串/部分匹配/ReDoS延时 | VULN-INPUT-REGEX-01 |
| ATK-INPUT-INVALIDSTRUCT-01（`input-invalidstruct-benign-malformed.md`） **[Inferred]** | 命中`VULN-INPUT-INVALIDSTRUCT-01` + 可观察解析结果/异常 | 不限语言(JSON/XML/CSV/协议解析) | 良性畸形结构输入证明无效结构处理失效——畸形JSON/XML观察崩溃/异常 | VULN-INPUT-INVALIDSTRUCT-01 |
| ATK-RES-CONSUMPTION-01（`res-consumption-benign-probe.md`） **[Proposed]** | 命中`VULN-RES-UNCONTROLLED-01` + 端点可达 | 不限语言/框架，所有Web框架 | 良性资源消耗探测证明DoS——略大/略高频请求确认无413/429 | VULN-RES-UNCONTROLLED-01 |
| ATK-RES-ITERATION-01（`res-iteration-benign-timeout.md`） **[Proposed]** | 命中`VULN-RES-ITERATION-01` + 循环受外部输入影响 | 不限语言/框架 | 良性超时证明过度迭代DoS——10倍迭代输入测量响应时序 | VULN-RES-ITERATION-01 |
| ATK-RES-RECURSION-01（`res-recursion-benign-depth.md`） **[Proposed]** | 命中`VULN-RES-RECURSION-01` + 递归深度受外部输入影响 | Python/Java/C/C++/JavaScript/Go等 | 良性深度嵌套证明递归失控——略深于默认限制的嵌套JSON | VULN-RES-RECURSION-01 |
| ATK-RES-COMPLEXITY-01（`res-complexity-benign-redos.md`） **[Proposed]** | 命中`VULN-RES-COMPLEXITY-01` + 正则含回溯风险 | Python re/Java regex/JS RegExp/PHP preg等 | 良性ReDoS探测证明算法复杂度DoS——30字符回溯触发输入 | VULN-RES-COMPLEXITY-01 |
| ATK-RES-FREQUENCY-01（`res-frequency-benign-burst.md`） **[Proposed]** | 命中`VULN-RES-FREQUENCY-01` + 端点可达 | 不限语言/框架，所有Web框架 | 良性突发请求证明速率限制缺失——20次/秒确认无429 | VULN-RES-FREQUENCY-01 |
| ATK-RES-UAF-01（`res-uaf-benign-dangling.md`） **[Proposed]** | 命中`VULN-RES-UAF-01` + 可触发释放后使用路径 | C/C++(ASan)/Python/Java/Go等 | 良性悬垂引用证明释放后使用——崩溃/异常而非代码执行 | VULN-RES-UAF-01 |
| ATK-CFLOW-OPENREDIRECT-01（`cflow-openredirect-benign-external.md`） **[Proposed]** | 命中`VULN-CFLOW-OPENREDIRECT-01` + 重定向参数可控 | 不限语言/框架，所有支持HTTP重定向的框架 | 良性外部URL证明开放重定向——example.com而非钓鱼站点 | VULN-CFLOW-OPENREDIRECT-01 |
| ATK-CFLOW-WORKFLOW-01（`cflow-workflow-benign-skip.md`） **[Proposed]** | 命中`VULN-CFLOW-WORKFLOW-01` + 后续步骤端点可直接访问 | 不限语言/框架 | 良性跳步证明工作流绕过——直接请求后续步骤确认200 | VULN-CFLOW-WORKFLOW-01 |
| ATK-INFO-EXPOSURE-01（`info-exposure-benign-probe.md`） **[Proposed]** | 命中`VULN-INFO-EXPOSURE-01` + API端点可达 | 不限语言/框架，所有Web框架 | 良性API请求证明敏感字段暴露——检查响应含password_hash | VULN-INFO-EXPOSURE-01 |
| ATK-INFO-OBSERVABLE-01（`info-observable-benign-enumeration.md`） **[Proposed]** | 命中`VULN-INFO-OBSERVABLE-01` + 认证端点对不同输入产生可观察差异 | 不限语言/框架 | 良性用户枚举证明可观察差异——1个存在+1个不存在用户比较错误 | VULN-INFO-OBSERVABLE-01 |
| ATK-INFO-COVERT-01（`info-covert-benign-timing.md`） **[Proposed]** | 命中`VULN-INFO-COVERT-01` + 高/低安全操作共享资源 | 不限语言/框架（通常需本地访问） | 良性时序测量证明隐蔽信道——测量可观察差异而非提取密钥 | VULN-INFO-COVERT-01 |
| ATK-AC-OWNERSHIP-01（`ownership-hijack-benign.md`） **[Inferred]** | 命中`VULN-AC-OWNERSHIP-01` + 可使用两个不同所有者身份 | Web/API/多租户应用 | 双身份良性操作证明所有权校验缺失 | VULN-AC-OWNERSHIP-01 |
| ATK-AC-PERM-READ-01（`permission-read-benign.md`） **[Inferred]** | 命中`VULN-AC-PERM-ASSIGN-01` + 可用低权限本地主体读取测试文件 | Unix/Linux文件系统及跨平台文件API | 用良性测试文件证明过宽权限允许非预期读取 | VULN-AC-PERM-ASSIGN-01 |
| ATK-AC-PHYSICAL-01（`physical-access-benign-probe.md`） **[Inferred]** | 命中`VULN-AC-PHYSICAL-01` + 可授权检查物理接口 | 硬件、IoT、嵌入式与终端设备 | 非破坏性检查调试/USB/机箱接口的物理可达性 | VULN-AC-PHYSICAL-01 |
| ATK-AC-PRIVILEGE-01（`privilege-escalation-benign.md`） **[Inferred]** | 命中`VULN-AC-PRIVILEGE-01` + 可观察放弃权限后的身份 | Unix/Linux系统编程与容器入口 | 良性身份检查证明进程仍保留或可恢复特权 | VULN-AC-PRIVILEGE-01 |
| ATK-AUTHN-BRUTE-01（`brute-force-rate-test.md`） **[Inferred]** | 命中`VULN-AUTHN-NO-RATELIMIT-01` + 使用测试账户和有限请求 | 所有认证端点 | 小规模频率测试证明认证端点缺少限速 | VULN-AUTHN-NO-RATELIMIT-01 |
| ATK-AUTHN-BYPASS-01（`auth-bypass-benign.md`） **[Inferred]** | 命中`VULN-AUTHN-BYPASS-01` + 可使用测试身份 | Web/API/桌面/移动认证流程 | 使用无效测试凭证证明认证逻辑绕过 | VULN-AUTHN-BYPASS-01 |
| ATK-AUTHN-CRED-LEAK-01（`credential-exposure-benign.md`） **[Inferred]** | 命中`VULN-AUTHN-CRED-PROTECT-01` + 使用合成凭证 | 所有凭证存储与处理流程 | 用合成凭证证明日志、存储或响应泄露 | VULN-AUTHN-CRED-PROTECT-01 |
| ATK-AUTHN-ID-PREDICT-01（`session-prediction-benign.md`） **[Inferred]** | 命中`VULN-AUTHN-INSECURE-ID-01` + 可生成多个测试标识符 | 会话与令牌系统 | 比较测试标识符序列证明其可预测 | VULN-AUTHN-INSECURE-ID-01 |
| ATK-AUTHN-LOCKOUT-DOS-01（`lockout-dos-benign.md`） **[Inferred]** | 命中`VULN-AUTHN-LOCKOUT-01` + 使用专用测试账户 | 所有账户锁定实现 | 有限失败尝试证明第三方可锁定指定账户 | VULN-AUTHN-LOCKOUT-01 |
| ATK-AUTHN-PASSHASH-01（`pass-the-hash-benign.md`） **[Inferred]** | 命中`VULN-AUTHN-PASSHASH-01` + 使用合成凭证哈希 | 自定义认证、遗留协议与API | 提交合成测试哈希证明其被当作凭证接受 | VULN-AUTHN-PASSHASH-01 |
| ATK-AUTHN-SESSION-FIXATION-01（`session-fixation-benign.md`） **[Inferred]** | 命中`VULN-AC-USERMGMT-01` + 可比较认证前后会话ID | 有状态会话框架 | 比较认证前后测试会话证明会话标识未重新生成 | VULN-AC-USERMGMT-01 |
| ATK-AUTHN-STALE-SESSION-01（`stale-session-benign.md`） **[Inferred]** | 命中`VULN-AUTHN-SESSION-LIFECYCLE-01` + 可执行登出或改密 | 有状态会话与令牌系统 | 复用测试会话证明安全事件后仍有效 | VULN-AUTHN-SESSION-LIFECYCLE-01 |
| ATK-AUTHN-WEAK-CRED-01（`weak-credential-benign.md`） **[Inferred]** | 命中`VULN-AUTHN-WEAK-CRED-01` + 使用专用测试账户 | 所有认证系统 | 用弱测试凭证证明策略未执行 | VULN-AUTHN-WEAK-CRED-01 |
| ATK-AUTHZ-OBJECT-CROSS-01（`object-level-identity-cross.md`） **[Inferred]** | 命中`VULN-AUTHZ-OBJECT-LEVEL-01` + 可使用两个测试身份 | Web/API/ORM/多租户应用 | 双身份交叉访问良性对象证明IDOR | VULN-AUTHZ-OBJECT-LEVEL-01 |

## 3. 单个知识条目内部结构规范

**文件组织**：每个知识条目是独立小文件，复用#16已定的"小文件"哲学。分类粒度当前未定，条目数量较少时可直接放在`attack-patterns/`根目录下；增长到需要分类时，按第7节的规模应对方案拆分。

**模板**：编写新条目时参考 [`_template.md`](_template.md)（模板不计入正式知识条目，不构成检测能力）。

**内部结构**：仍以**Source / Propagation / Sanitizer / Sink**四段为骨架组织，对应#4已确立的六项验收基线字段——但攻击模式条目不重复记录对应vuln-pattern条目已写过的S/P/S/S细节（通过第2节的交叉引用列查即可，避免消费方每次重新匹配，#15已确认的原则），而是在此骨架基础上补充"如何把这条链转化为具体可演示动作"的两个层次：

| 条目内部段落 | 对应#4六项验收基线 | 该段应记录的内容 |
|---|---|---|
| （承接）Source/Propagation/Sanitizer | 可控性 + 可达性 + 传播完整性 | 不重复记录，仅通过交叉引用指向对应vuln-pattern条目 |
| Sink（利用化） | 可利用性（exploitable） | 具体的利用步骤：怎么构造输入/触发调用，使危险操作产生可观察的、能证明"确实被利用"的效果 |
| 证明形态与危害最小化 | 可复现性（reproducible）+ 影响成立（impact） | 该手法对应的证明形态（如"崩溃输入+调用栈"/"构造请求+响应差异"/"两个身份的对比访问"，`exploit-proof/SKILL.md`已确立不存在通用模板套所有类型）+ 该手法的危害最小化处置方式（良性标记/占位符凭证，#6已确立原则） |

条目应同时标注该手法对应#6判定的"已执行模式"还是"推导模式"哪一类场景（即该手法是否需要真实运行时环境才能落地，还是仅能产出走查说明），供#6选用时直接判断适用性。

## 4. 强制显式查阅纪律（核心纪律，不得含糊）

- "要不要查、查了没有"不能交给#6自由裁量。#6在选用某个可选利用手法（如猴子补丁式依赖模拟）时，产出必须显式写明**查了哪个条目ID**。
- 查不到匹配条目时，必须显式写**"未匹配，可能是新利用手法，本次采用临时实现"**，不能含糊过去或默默跳过不提。
- 引用的条目ID必须可被机械核对——是否真实存在于本索引表格里（应用#17已确立的T2机械核对能力）。核对对象是"引用的ID是否存在"这件事本身，不涉及"这次利用手法用得对不对"，后者仍是#6自己的职责。核对由宿主Agent按#17 T2机械核对能力执行——检查ID是否存在于本索引表格中即可，不需要GenSource自建验证程序。

## 5. 引用分级

复用#7/#11已确立的**Observed / Inferred / Proposed**三段式标签，不新造标签体系。在本目录场景下的含义：

- **Observed**：该利用手法在当前目标环境下已经过`exploit-proof/SKILL.md`步骤C.6"打包后收尾检查"验证复现（对应#6的已执行模式）。
- **Inferred**：基于对应vuln-pattern条目推断该利用手法理论适用，尚未做打包后收尾检查（对应#6的推导模式——清楚标注"基于代码推理推导、未独立执行"，不得包装成已执行）。
- **Proposed**：条目本身是新提出的利用手法建议，尚未在任何真实案例中验证过。

**标注归属**：这个分级标注写在#6产出的PoC记录里（描述"这次具体审计怎么用这条知识"），不是本索引文件自身的字段。

## 6. 不采纳向量/混合检索

复用06号早期跨竞品打分框架已确立、24号（#15）再次确认仍有效的结论：**F1（纯Markdown小文件+表格索引）为基座不动摇，F2（向量/混合检索）明确不采纳**。

**元星刃反例**（06号/24号已引用）：元星刃建成了CWE-7全量XML+BM25/Chroma混合检索能力，但8个worker的system prompt完全没有引用检索结果——"知识库与审计流程完全脱钩"（`09-yuanxingren.md`§9）。这证明"有检索能力"和"检索能力真正驱动判断"是两件不同的事，不能想当然认为"上了向量库就变强"。

本目录索引同样始终保持"表格化+扫一眼就能判断该不该细看"的哲学，不引入语义相似度检索或混合检索基础设施。

## 7. 索引规模过大时的应对

复用#12（`docs/research/decision/25-category12-scale-cost-management-spec.md`第4节）已确认的方案：**索引本身分层拆分成"子类索引+索引的索引"，不引入向量检索**。

- 当本文件这一份表格本身也大到难以被"扫一眼"评估时，按分类维度（如按对应vuln-pattern的CWE大类、按语言/框架，具体分类维度留待实际条目积累后确定）拆出`attack-patterns/<category>/_index.md`子类索引，每份子类索引仍是同样的表格格式（第2节列定义不变）。
- 拆分后，本文件（`attack-patterns/_index.md`）升级为"索引的索引"——只列每个子类索引的名称/条目数量概览/相对路径链接。
- **语言覆盖度老实披露**（复用#13已确立原则）：利用手法的语言相关性通常比漏洞模式更强，按语言/框架拆分后若某语言条目数量明显偏少，消费方引用时必须显式披露完整性置信度较低，不能装作深度一致。
- **中文文本匹配caveat**（复用#13已披露的LANG-04）：若"触发信号"或摘要涉及中文文本匹配，标准按空格分词的正则匹配对中文不生效，需要单独处理，具体方式留待实际编写时确定。

## 8. 待办声明

分类粒度、条目文件具体命名规则、机械核对的具体实现，均留待未来实际编写知识条目/contracts层设计时确定，本文件不提前杜撰。
