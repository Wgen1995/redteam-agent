# path-traversal ｜ 路径穿越（CWE-22）

> band: 1 ｜ 模式表: `patterns/path-traversal-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/path-traversal/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 任意写且落点在可执行路径（webroot/cron/库目录）→ Critical；任意读且可及密钥/凭据/源码 → High；穿越被 canonical 包含检查钳制在基目录内的读写 → Medium；仅能探测文件存在性 → Low（前提引文）

## ① 定义与危害
外部可控的路径片段未经规范化校验拼入文件系统访问，攻击者用 `../`（或绝对路径注入/符号链接/ZIP 条目名）把访问点移出预期基目录——任意文件读（密钥、配置、源码）、任意写（向 webroot 落脚本→RCE）、受限写覆盖（篡改启动脚本/定时任务）、越租户访问。依据：CWE-22；CVE-2021-43798（Grafana 任意读）、CVE-2020-17519（Flink 任意读）、CVE-2019-5418（Rails 任意读）、CVE-2021-42013（Apache 穿越→RCE）、zip-slip（Snyk 2018 披露，解压落盘穿越）。

## ② Source
HTTP 参数/路径变量/头部/_body_、**上传文件名（multipart originalFilename——浏览器可整体伪造，含 `../` 段）**、消息体（external_message）、**存储回读（persisted_read：DB 存的文件名/相对路径被回读后拼路径——二阶穿越）**。URL 解码（`%2e%2e`→`..`）通常在框架入口完成，Source 取值点看到的是解码后形态——编码类绕过见 ⑧，不在 Source 层重复计。

## ③ Sink 模式表指针
`patterns/path-traversal-java.pattern` / `path-traversal-ts.pattern` / `path-traversal-python.pattern`（机器直读，逐行一条，不并串；枚举形态=「路径构造/访问点含拼接」，`new File(tainted)` 单参无拼接、`resolve(tainted)` 无拼接等低频形态见 ⑧ 漏报单 B11）。

## ④ Propagator
字符串拼接（`+`/模板串/f-string）、`String.format`、StringBuilder.append 链、`Paths.get(a).resolve(b)`/`os.path.join`/`path.join` 参数透传、`URLDecoder.decode`（还原 `%2e%2e` 不改变可控性）、**`entry.getName()`（ZIP/压缩条目名——可控性等同打包者）**、`File(parent, child)` 的 child 透传（绝对 child 丢弃 parent）。跨字段保守传播。

## ⑤ Sanitizer（决策表三值）
canonical 后基目录包含检查（`toRealPath().startsWith(realBase)` / `os.path.realpath` 后逐段比较，两边均为解析产物）→ **强**（前提：发生在读取之前，见 C2 时机）；白名单枚举/服务端生成名（UUID 改名、id→路径映射表）→ **强**；`basename`/`FilenameUtils.getName` → **上下文条件**（POSIX 剥离 `/` 段有效，Windows `..\` 分隔仍穿——只产 hint，禁 kills）；normalize 前的 `startsWith(基目录字符串)` → **弱**（前缀撞库+`..` 反解）；黑名单 `replace("../","")` → **弱**（`....//` 单次替换后复原）；`if(strict)` 才启用 → **上下文条件（只产 hint，禁 kills，挂 requires_config）**。**多段净化看全部：读取之后才 normalize 不构成净化。**

## ⑥ 判定流程（编号条目）
C1 路径片段是否外部可控（参数/路径变量/上传文件名/回读）？｜期望引用:入口签名与取参行、上传元数据取值行｜推翻反例:实参为编译期常量或服务端枚举映射产出｜反向:文件名入库后被回读再拼（persisted_read）
C2 路径归一化发生在读取之前还是之后？｜期望引用:normalize/toRealPath/realpath 调用行与 open/new File 行的先后顺序｜推翻反例:先 toRealPath 再以解析结果 open（读前归一化成立）｜反向:open(拼接路径) 之后才对结果 normalize（读后归一化无效——访问已发生）
C3 基目录包含检查可否被 `..` 绕过？｜期望引用:startsWith/canonical 包含检查行及其比较对象（字符串前缀或已解析 Path）｜推翻反例:两侧均为 canonical 解析后的绝对路径且按路径段比较｜反向:字符串 startsWith(base)、或 canonical 后与未解析 base 比较（../ 可反解出基目录前缀）
C4 读取目标可否被符号链接重定向？｜期望引用:用 toRealPath（解析 symlink）还是 toAbsolutePath、基目录内是否存在可写目录｜推翻反例:无 symlink 且目录不可写｜反向:上传/缓存目录可写→先落软链再触发读取（含检查-打开间隙换链的 TOCTOU）
C5 ZIP/压缩条目名是否未校验直接拼入落盘路径（Zip Slip）？｜期望引用:getNextEntry/entry.getName 与 new File/Files.write 的拼接行｜推翻反例:条目名经 canonical 包含检查或逐段白名单｜反向:new ZipInputStream 存在但文件内无任何条目名校验
C6 净化是否消除路径载荷形态（决策表查值）？｜期望引用:净化调用行+其叶子实现｜推翻反例:强净化且先于读取生效｜反向:净化在假分支/常量条件里，或 basename 用于 Windows 分隔语境
C7 入口可达且鉴权不拦截？｜期望引用:路由注解/拦截器配置｜推翻反例:内网-only 且有边界证据｜反向:默认放行配置
C8 读写方向与落点可观测？｜期望引用:读取内容的响应构造行/写入目录的部署属性｜推翻反例:读后不回显且无外带通道｜反向:写 webroot 或 cron 目录（无需回显即按 Critical）

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 id→路径走服务端枚举映射（`ALLOWED.get(id)` 取路径再拼）——输入只选键不构成路径片段，需 C1 反证引文。
FP-2 路径全部来自配置/环境变量（`props.getProperty("dir")` 拼服务端常量后缀）——非输入通道，需 C1 反证引文。
FP-3 上传已 UUID 改名（`UUID.randomUUID()` 作落盘名，originalFilename 只进元数据）——需改名行与落盘行的 OBS 链。
FP-4 日志/导出文件名由服务端变量拼（应用名+日期+轮转序号）——同 FP-2 判据。
FP-5 Python `open(path, 'a+')` 模式串含 `+` 的形态撞车（PT-P01 误命中）——枚举层噪音，VERIFY 看实参不含可控片段。
FP-6 常量子路径的 `Paths.get(BASE).resolve("固定名")` 链（PT-J13 命中）——需 C1 反证引文。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 Windows 分隔 `..\`（含混合 `../..\`）——POSIX `basename`/`FilenameUtils.getName` 不剥反斜杠段。
B2 URL 编码 `%2e%2e%2f`——检查发生在解码前、或解码层晚于检查时成立。
B3 双重编码 `%252e%252e%252f`——存在二次解码层（网关一次+应用一次）时成立。
B4 绝对路径注入：子路径以 `/`（或盘符 `C:\`、UNC）开头时，`resolve`/`File(parent, child)` 丢弃基目录直接命中绝对目标。
B5 null 截断 `%00`——老 JDK/老 PHP 截断后缀校验；新运行时按字面文件名处理，需先证环境再报。
B6 UNC 路径 `\\attacker\share`（Windows）——绕开盘符白名单并向外带文件内容（SMB 认证）。
B7 软链：基目录内可写→先落 symlink 指向目标再触发读取；检查-打开间隙换链可破 realpath 检查（TOCTOU）。
B8 前缀撞库：`startsWith("/app/data")` 被 `/app/data-evil` 满足（非目录边界比较）。
B9 ZIP 条目名含 `../` 或绝对名（`/etc/cron.d/x`）——`new File(dir, name)` 不拒绝穿越段（Zip Slip）。
B10 二阶：文件名入库（存 `../../` 形态），回读侧拼路径（追 persisted_read）。
B11 低频形态枚举不命中：`new File(tainted)` 单参无拼接、`resolve(tainted)` 无拼接、`File(parent, child)` 双参、`Files.writeString/copy/move`——band 卡靠 langpack source 同文件共现补抓。

## ⑨ 利用前提与定级阶梯
见页首。High 验收：给出一次可读出密钥/源码的具体路径与回显证据；Critical 验收：写入点在执行路径且有执行触发证据。band:1 与 band:0 的差别：发卡前必须闭合「归一化时机（C2）/包含检查强度（C3）/平台分隔符（C6）」三问，不能只凭拼接形态。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 路径拼接仅固定前缀+basename 归一引文在位，或落点目录不可控 → 降 low

## ⑩ 根因修复
读前 canonical + 基目录逐段前缀比较（比较对象两侧同为 realpath 产物）；上传一律服务端生成落盘名（UUID/序号）；解压逐条目 canonical 校验；路径参数改白名单 id 映射；禁用 `File(parent, child)` 的"child 自动相对"假设（绝对 child 丢弃 parent）；路径拼接入口处 lint 门禁。

## ⑪ 跨边界提示
Egress 侧把拼接好的相对路径片段传给下游服务/对象存储网关（下游再本地拼接）；Ingress 侧消息体直接携带文件名进落盘；多租户共享基目录时穿越即越租户（联动 authz 卡）；CI/CD 产物名入库后由部署侧回读拼路径（二阶）。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 12/24/7、python 10/11/4、ts 7/10/4
`fixtures/enum/path-traversal/{lang}/manifest.tsv`（java 达标集：正例≥10/硬负例≥20/噪音≥5；ts/python 为起步集——见 classes/fixture-spec.md 三类语义）。
