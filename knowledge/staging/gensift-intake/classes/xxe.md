# xxe ｜ XML 外部实体注入（CWE-611）

> band: 0 ｜ 模式表: `patterns/xxe-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/xxe/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 外部实体可外带（file:// 读文件 / http(s) 内网探测，与 ssrf 卡合流）→ High；报错或盲外带（参数实体拼 URL）→ Medium–High；仅内联实体扩展（XML bomb / billion laughs，纯 DoS）→ Medium（前提引文）

## ① 定义与危害
XML 载荷在 DTD 中声明实体（含 SYSTEM/PUBLIC 外部实体与参数实体），解析器默认解析实体引用——攻击者用 `<!ENTITY x SYSTEM "file:///etc/passwd">` 读本地文件、用 `http://` 打内网（与 ssrf 卡合流）、用参数实体把机密拼进外带 URL（盲 XXE）、用内联实体嵌套扩展打崩解析器（billion laughs）。危害面：任意文件读、内网探测、凭据外带、DoS。依据：CWE-611；dom4j `parseText` 面历史案例 CVE-2020-10683；OOXML 内嵌 XML 解析面历史案例 CVE-2019-12415（Apache POI XSSFExportToXml）。

## ② Source
XML 载荷来源：请求体（application/xml / text/xml / SOAP）、SAML/SSO assertion 与 IdP metadata、webhook 回调 XML、消息队列 XML 载荷（external_message）、**上传工件回读（SVG / docx / xlsx 等 OOXML 本质是 zip 内 XML——"解析上传的 office 文档"即本类入口，联动 file-upload 卡）**、**存储回读（persisted_read——二阶：用户值入库后被拼进服务端 XML 模板再整体解析，XML 注入升实体注入）**。回读的 XML 字段默认 unknown 可控性，禁止在 VERIFY 中当"不可控"反证。

## ③ Sink 模式表指针
`patterns/xxe-java.pattern` / `xxe-ts.pattern` / `xxe-python.pattern`（机器直读，逐行一条，不并串）。工厂创建点（`newInstance()` / `new SAXReader(`）与读点（`newDocumentBuilder` / `createXMLStreamReader` / `unmarshal` / `fromstring`）都进表——**枚举层不区分安全/危险配置**（同一 API 的硬化用法是 noise 不是 neg，见 classes/fixture-spec.md §2），配置判据在 C2/C3。表外未列举家族（TransformerFactory / SOAP MessageFactory / SAXSource 直构 / xml.sax / sax.js / libxmljs——见 ⑧ B7）走扩清单，不进 v1 模式表。

## ④ Propagator
字节流/字符串透传（`getInputStream` / `IOUtils.toByteArray` / `request.body` / `fs.readFileSync` / `await file.read()`）；OOXML 解包（zip entry → 内层 XML 流）；**XML 模板拼接**（服务端常量 XML 片段 + 用户值 + 整体再 parse——拼接点离解析点可隔多层）。Base64/hex 只改载体不改语义——**编码不是净化**。跨字段/跨方法保守传播。

## ⑤ Sanitizer（决策表三值——解析器工厂配置判据）
**通用规则：默认工厂≠安全。** `DocumentBuilderFactory.newInstance()` / `SAXParserFactory.newInstance()` / `XMLInputFactory.newInstance()` / dom4j `SAXReader` / JDOM `SAXBuilder` / Jackson `XmlMapper` 在主流 JDK（含 8/11/17/21 LTS）默认仍解析外部实体——"升级了 JDK/依赖"不构成净化证据，需逐配置行 OBS。

| 配置原语 × 载荷形态 × 解析器家族 → 判值 | 逐版本注意 |
|---|---|
| `disallow-doctype-decl=true`（http://apache.org/xml/features/disallow-doctype-decl）× 任意 DTD → **强**（连内联实体/参数实体一并禁） | Xerces 系（JDK 默认/dom4j/JDOM）支持；SAXReader/SAXBuilder 需 setFeature 显式开 |
| `external-general-entities=false` **且** `external-parameter-entities=false`（http://xml.org/sax/features/...）→ **强组合** | 单关 general 仍留参数实体外带与 XML bomb（B2）——单独一条只算**上下文条件** |
| StAX：`SUPPORT_DTD=false`（javax.xml.stream.supportDTD）或 `IS_SUPPORTING_EXTERNAL_ENTITIES=false` → **强** | XMLInputFactory 走 setProperty 非 setFeature；Woodstox 同名属性 |
| JAXP 1.5 属性 `ACCESS_EXTERNAL_DTD` / `ACCESS_EXTERNAL_SCHEMA` = 空串 → **强** | 仅 JDK 8+ / 7u40+；对 StAX 是 `javax.xml.stream.supportDTD` 之外的补充面 |
| `FEATURE_SECURE_PROCESSING=true` → **上下文条件（只产 hint，禁 kills，挂 requires_config）** | JDK 8+/7u40+ 才联动把 accessExternal* 默认收空；老 JDK 只限幅不断实体；第三方 Xerces 直用不跟随 JVM 标志 |
| `disable-xml-external-entity` 类同义开关（部分封装库/第三方解析器）→ **强（需查该库文档确认语义）** | 命名不统一，VERIFY 时以库版本的手册引文为准 |
| JAXB `Unmarshaller.unmarshal(SAXSource)` 且 SAXSource 由已硬化 SAXParser 构造 → **强** | **Unmarshaller 自身没有实体开关**——在 unmarshaller 上找 setFeature 找不到不是漏配是常态（B3 前置） |
| lxml `XMLParser(resolve_entities=False)`（或 defusedxml 全家）→ **强** | lxml 默认 `resolve_entities=True`；`no_network=True` 是默认但只断 http/ftp 面，**file:// 不在其列** |
| 黑名单（自写正则禁 `<!ENTITY`/`SYSTEM`）/ 只限编码 / 只限大小 → **弱** | 载荷可换行/注释分片/UTF-16 混淆（B8）；形态与净化不匹配 |
| `if(strictProfile)` 才硬化 → **上下文条件（只产 hint，禁 kills）** | 显式挂 requires_config |

**Python stdlib 注意**：xml.etree / minidom（expat）不解析外部实体（未挂外部实体 handler），但旧版本对内联实体扩展无限幅（billion laughs）——stdlib 命中降档不 kills，判值**上下文条件**，以本机 Python/expat 版本实测为准。**TS/JS 注意**：DOMParser（浏览器/jsdom/linkedom 语义）与 xml2js/sax.js 默认不解析外部实体；真实风险位是 libxml 系绑定（libxmljs 开 noent/recover）与启用 XInclude 的管线——判值同样**上下文条件**，需 OBS 运行环境。**多段净化看全部：setFeature 抛异常被 catch 后继续 parse = 未净化（见 C2 反向）。**

## ⑥ 判定流程（编号条目）
C1 XML 载荷是否外部可控（请求体/SOAP/SAML/上传工件/消息/回读模板）？｜期望引用:入口签名与取流行、上传工件回读行｜推翻反例:载荷为服务端编译期常量或互信下发（签名验证行）｜反向:用户值拼进服务端 XML 模板后整体解析（persisted_read）
C2 解析器工厂是否逐项配置了实体禁用（对照 ⑤ 表逐行核销）？｜期望引用:工厂创建行到 parse 行之间的全部 setFeature/setProperty 语句｜推翻反例:disallow-doctype-decl 或"双 external-entities 关 + SUPPORT_DTD=false"等效强组合齐备且先于 parse｜反向:仅 FEATURE_SECURE_PROCESSING、仅 external-general-entities 单关、或 setFeature 包在 catch 里吞异常继续 parse
C3 是否把"默认工厂/新版本依赖"误当安全（默认工厂≠安全）？｜期望引用:工厂创建行与 parse 行之间的语句序列（零配置即未净化）｜推翻反例:平台统一硬化基线——JVM 启动参数 accessExternal* 置空/容器 security 配置（需启动配置 OBS，代码内不可见时不构成 kills）｜反向:注释或 commit message 声称"升级后默认安全"、依赖版本升级即认为已修
C4 载荷会流经几个解析层（主解析器之外：Schema 校验器内嵌解析/Transformer/XInclude/XPath document()）？｜期望引用:newValidator().validate / transform / setXIncludeAware / xi:include 行｜推翻反例:单层主解析且 C2 已核销｜反向:Validator.validate(Source) 内部再起未配置解析器、setXIncludeAware(true) 后 xi:include href 直取外部
C5 外带通道是否存在（实体值回显/报错透出/参数实体盲外带）？｜期望引用:响应构造行、异常消息透出行、错误日志回写行｜推翻反例:统一错误吞噬且无差分无出网｜反向:SYSTEM 实体值出现在 DOM 节点并回写客户端、报错把实体内容带回
C6 入口可达且鉴权不拦截？｜期望引用:路由注解/拦截器配置｜推翻反例:内网-only 且有边界证据｜反向:webhook/SOAP 网关默认放行配置
C7 危害是外带（file:// 读、http 内网）还是仅 DoS（内联实体扩展无外部解析）？｜期望引用:实体形态（SYSTEM/参数实体 vs 纯内联嵌套）与出网证据｜推翻反例:仅 billion laughs 形态且 C5 全阴｜反向:存在 SYSTEM 实体且 C5 回显成立
C8 载荷是否只来自内部可信来源（FP 卡触发问句）？｜期望引用:常量定义行/模板生成链/下发方签名验证行（来源证据）｜推翻反例:可指出请求通道进入 XML 流的具体行｜反向:来源不可 OBS 时按 unknown 可控性处理，不得反证

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 只解析内部可信 XML（服务端常量配置/自产模板/互信系统下发）——**需来源证据**（常量定义行 OBS 或签名验证行），仅"未见用户输入拼入"不构成反证。
FP-2 现代封装工具类内部已 disallow-doctype-decl + 双 external-entities 关——需 OBS 到封装方法体内 setFeature 全量（不是封装名）。
FP-3 平台统一硬化（JVM 系统参数 accessExternal* 置空 / 容器安全基线）——需启动配置 OBS；代码内不可见时只产 hint 禁 kills。
FP-4 Python stdlib xml.etree/minidom 不解析外部实体——枚举命中仍成立，定级降档处理；需本机版本验证记录。
FP-5 TS 侧 DOMParser/xml2js 默认不解析外部实体——仅当 OBS 到运行环境为 DOM 实现（jsdom/linkedom/浏览器）且非 libxml 绑定时降档。
FP-6 测试代码/内部工具解析固定样本文件——需文件来源非请求通道的证据（路径常量 + 无取流行）。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 XInclude 绕 DOCTYPE 禁令：disallow-doctype-decl 只禁 DTD；`setXIncludeAware(true)`（或 StAX XInclude 属性、XSLT 管线）启用后 `<xi:include href="file:///etc/passwd">` 直读（对 C4）。
B2 参数实体外带（盲 XXE）：外部 DTD 中参数实体把机密拼进 SYSTEM URL——external-general-entities=false 单关封不住，需 external-parameter-entities=false 或 SUPPORT_DTD=false（对 C2）。
B3 Schema 校验器内嵌解析：`newValidator().validate(Source)` / `newSchema(Source)` 内部再起一个未配置解析器——主解析器配置不传递（对 C4）；JAXB unmarshal 的内嵌 SAX 同理。
B4 报错通道：解析异常把实体值带回（error message 含 SYSTEM 解析结果）——统一错误页不吞 entity 值时即盲外带成立（对 C5）。
B5 二阶：用户值入库后被拼进服务端 XML 模板整体解析——追 persisted_read（对 C1 反向）。
B6 scheme 变体：`file://`、`jar:file://`、`netdoc:`（Java 特有）、相对 SYSTEM 引用；expect:// 类仅在对应绑定存在时成立。
B7 表外家族：TransformerFactory（XSLT `document()` / import/include）、SOAP MessageFactory、SAXSource 直构、xml.sax、sax.js、libxmljs（noent/recover 开启）、OOXML 处理库（POI 等，解包即内层 XML）——v1 模式表未列，靠 B 清单扩表。
B8 文本混淆绕黑名单：DTD 内换行/注释分片（`<!EN<!--x-->TITY`）、UTF-16 载荷、BOM——对自写 `<!ENTITY` 正则黑名单（⑤ 弱档）。
B9 SVG 上传即 XXE 载荷（`<!ENTITY` 内嵌 SVG）——上传面与解析面分离时两条链都要走（联动 file-upload C5）。

## ⑨ 利用前提与定级阶梯
见页首。High 验收：给出实体声明到回显/外带 URL 的完整证据链（含 C2 净化核销失败的引文）。Medium（DoS 档）必须有 C7 内联形态引文。band:0 与 band:1 的差别：本类只凭"默认工厂 + 可控载荷"两问即可发卡——C2/C3 任一失败即成立，不需要闭合全部八问。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 解析器禁外部实体配置引文（disallow-doctype-decl/features）或 XML 源仅内部可信生成 → 降 low

## ⑩ 根因修复
平台统一 SecureXmlFactory 工具类（disallow-doctype-decl + external-general/parameter-entities 双关 + SUPPORT_DTD=false + ACCESS_EXTERNAL_* 置空 + FSP，全部先于 parse 且不吞异常）；JVM 全局参数（javax.xml.accessExternalDTD/SCHEMA=空）兜底；JAXB 走 SAXSource 注入硬化解析器而非裸 unmarshal；Python 侧 defusedxml / lxml resolve_entities=False；lint 门禁禁止业务代码直连 `newInstance()` 裸解析；OOXML 处理库升级到已修版本。

## ⑪ 跨边界提示
Egress 侧 XML 模板拼用户值后跨服务传递再解析（二阶）；消息队列/SOAP 网关 XML 载荷跨信任边界（每个消费端独立核销 C2）；SAML/IdP metadata 是 Ingress 侧不可信来源（签名验证≠实体禁用）；上传工件解析把 file-upload 卡与本卡串成链（C1 反向 + file-upload C5）。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 13/24/6、python 9/12/4、ts 8/12/4
`fixtures/enum/xxe/{lang}/manifest.tsv`（java 达标集：正例≥10/硬负例≥20/噪音≥5；ts/python 起步集——见 classes/fixture-spec.md 三类语义；manifest 含出处列必填）。
