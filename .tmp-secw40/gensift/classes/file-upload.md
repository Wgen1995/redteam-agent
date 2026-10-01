# file-upload ｜ 不受限文件上传（CWE-434）

> band: 1 ｜ 模式表: `patterns/file-upload-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/file-upload/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 存储路径 web 可达且扩展名可解析执行（jsp/jspx/php/aspx/asa）→ Critical（RCE）；web 可达 + HTML/SVG（inline content-type）→ High（存储 XSS）；覆盖服务端回读的配置/脚本/.htaccess/web.config → High–Critical；解析二次利用命中（ImageMagick MVG/MSL、exiftool、解压穿越）→ Critical；仅对象存储私有桶不回读不解析 → Medium 以下（前提引文）

## ① 定义与危害
上传接口把客户端完全可控的文件本体与元数据（originalFilename、Content-Type、大小）直接落到可预测位置，校验层可整体绕过——攻击者落 webshell（web 可达 + 可解析扩展即 RCE）、落 HTML/SVG 打存储 XSS、覆盖配置与启动脚本、投递解析器载荷（ImageMagick/exiftool/解压炸弹）。依据：CWE-434；解析二次利用历史案例 CVE-2016-3714（ImageTragick）、CVE-2021-22204（ExifTool）；multipart 边界解析面历史案例 CVE-2017-5638（Struts2 Jakarta multipart，Content-Type 头触发）。

## ② Source
multipart 文件本体与全部元数据（`getOriginalFilename()`/`file.originalname`/`f.filename`/`Part.getSubmittedFileName()`/`getContentType()`——**浏览器可整体伪造，文件名含路径段时联动 path-traversal 卡**）、base64-in-JSON 上传（无 multipart 形态的等价入口）、分片/直传对象存储 + 回调（callback 携带可控存储名）、**存储回读（persisted_read——二阶：入库文件名/URL 被回读后用于下载、预览、删除——联动 path-traversal）**。元数据默认 unknown 可信度，禁止在 VERIFY 中当"可信"反证。

## ③ Sink 模式表指针
`patterns/file-upload-java.pattern` / `file-upload-ts.pattern` / `file-upload-python.pattern`（机器直读，逐行一条，不并串）。枚举形态 = 上传类型/中间件标记 + 落盘调用（transferTo/write/save/writeFile/copyfileobj）。安全用法（UUID 改名、白名单、大小限）与危险用法在同一 API 上——枚举层不区分（noise 不是 neg，见 classes/fixture-spec.md §2），判别在 C2/C3/C4。表外未列举家族（busboy、multiparty、@FormDataParam/JAX-RS、OkHttp 服务端接收、Tornado `self.request.files`——见 ⑧ B11）走扩清单，不进 v1 模式表。

## ④ Propagator
文件名/扩展名透传（`getOriginalFilename()` 返回值直接或拼接后进路径构造）；字节流搬运（`getInputStream`/`getBytes`/`chunks()`/`await file.read()` → write/copy）；分片字段拼装（chunk index + name 决定最终路径）；入库文件名回读后再用（persisted_read）。**Content-Type 与文件名同属客户端声明——两者透传到校验层不构成任何净化**。跨字段/跨方法保守传播。

## ⑤ Sanitizer（决策表三值）
**扩展名白名单（大小写归一 + 取最后一个点后段）→ 强**（仅当存储名同时服务端生成，见 C3）；**服务端重命名（UUID/序号）+ 非 web 可达目录/私有桶 → 强**（两段各自只算弱，合起来才是强——多段净化看全部）；**魔数/解析成功校验（ImageIO.read 成功、file 命令、python-magic）→ 强（对"仅媒体文件"目标）**，但解析器差异载荷（polyglot/B8）下单算**上下文条件**；MIME 白名单取自 `getContentType()` → **弱**（客户端可伪造，B4）；扩展名黑名单 → **弱**（双扩展/大小写/空字节全过）；`secure_filename`/`FilenameUtils.getName` → **上下文条件**（只封路径注入段，不封内容与扩展名语义；只产 hint，禁 kills）；大小/数量配额 → **上下文条件**（封资源面不封内容）；`if(config.strictUpload)` 才启用 → **上下文条件（挂 requires_config）**；前端/JS 侧扩展名检查 → **不算净化**（服务端不可 OBS 的控制为零）。

## ⑥ 判定流程（编号条目）
C1 文件本体与元数据是否外部可控（multipart/base64-JSON/分片/对象存储回调）？｜期望引用:入口签名、multipart 取值行、回调处理行｜推翻反例:载荷为服务端自产文件（定时导出等，需生成链 OBS）｜反向:文件名入库回读后再用于落盘（persisted_read）
C2 扩展名/MIME/魔数三层谁验了、验的是哪一层？｜期望引用:校验函数行与其输入源（文件名后缀 or getContentType() or 魔数探测）｜推翻反例:三层全验且白名单后缀 + 服务端生成存储名｜反向:仅 Content-Type 黑名单、MIME 取自客户端声明、仅前端校验、扩展名黑名单、大小写未归一
C3 存储名是否服务端重命名（UUID/序号），扩展名是否服务端从白名单映射？｜期望引用:落盘名构造行（transferTo/write/save/writeFile 的实参表达式）｜推翻反例:UUID 名 + 白名单后缀拼接且无客户端段｜反向:getOriginalFilename() 值（或其去路径段形态）直接作落盘名、双扩展保留、点结尾/尾空格形态
C4 存储路径是否 web 可达（webroot/静态资源映射/同 origin 直接 GET）？｜期望引用:落盘目录常量定义行与静态资源 handler/映射配置｜推翻反例:非 web 目录、对象存储私有桶、下载必须经鉴权控制器流式回吐｜反向:uploads/ 注册在 static handler 下、目录在应用服务器可执行映射内（jsp/php）、SVG 以 inline content-type 回吐
C5 解析二次利用是否存在（缩略图/转码/exif/杀毒/office 转 PDF/解压）？｜期望引用:处理管线调用行（ImageIO/Thumbnails/ImageMagick/exiftool/unzip/office 库）｜推翻反例:仅字节存储无任何再解析｜反向:ImageMagick 未禁 MVG/MSL/policy、老版本 exiftool、解压不校验条目名（Zip Slip 联动 path-traversal）
C6 校验与落盘之间是否存在竞态双写窗口（检查-提交间并发）？｜期望引用:校验行与 write 行的顺序、目标名是否可预测、是否先写后检再删｜推翻反例:临时不可达名落盘 + 校验后原子 rename，且最终名不可预测｜反向:先落 uploads/<可预测名> 再校验、同名分片乱序双写、删除失败后残留
C7 入口可达且鉴权/配额不拦截？｜期望引用:路由注解/中间件链、大小限制配置行｜推翻反例:内网管理面-only 且有边界证据｜反向:公开注册/头像接口默认放行
C8 上传后回读链（按存储名下载/预览/删除）是否存在？｜期望引用:下载与删除端点的取名行（request 参数 → 文件路径构造）｜推翻反例:无回读端点且不解析｜反向:回读名直接拼路径（转 path-traversal 卡）

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 服务端 UUID 重命名 + 非 web 目录存储（originalFilename 只进元数据）——**需 OBS**：改名行与目录/映射配置双证缺一不可。
FP-2 文件直转对象存储私有桶且无回读无解析——需存储 SDK 行与桶策略证据。
FP-3 仅内网管理后台上传且鉴权强——联动 authz 卡，需边界证据。
FP-4 上传即弃的临时分析流（写 tempfile 立即读删）——需生命周期证据（写-读-删同方法可 OBS）。
FP-5 Content-Type 判断出现在非上传方向（下载响应 setContentType）——形态撞车，VERIFY 看无落盘点。
FP-6 `InputStream.transferTo(response)` 下载方向（与 MultipartFile.transferTo 撞名）——形态撞车，VERIFY 看调用接收者是响应流。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 双扩展 `shell.jsp.png` / `shell.php.jpg`——web 服务器取第一后缀或解析漏洞（老 IIS/Nginx 空格文件名 `shell.php .jpg`）。
B2 大小写与尾部形态：`shell.pHp`（未归一即过）、`shell.php.`（Windows 剥尾点）、`shell.php `（尾空格）、`.php5/.phtml/.jspx` 变体入黑名单漏网。
B3 空字节截断 `shell.php%00.png`——老 JDK/老 PHP 截断后缀校验；新运行时按字面名处理，需先证环境再报。
B4 Content-Type 伪造：请求头 `image/jpeg` + jsp 本体——C2 只看客户端声明 MIME 即全过（对 C2 反向）。
B5 polyglot：JPEG 注释段嵌脚本、`GIF89a` 头 + PHP 体、SVG 内嵌 script、phar:// 包装、PPTX（zip）内嵌 web.xml 级条目——魔数校验与真实解析器不一致时过（对 C5）。
B6 竞态双写：先传合法名过检，在校验-落盘/删除窗口内二次写入同名（C6）；分片上传乱序拼接覆盖已检片段。
B7 解析二次利用载荷：ImageMagick MVG/MSL（CVE-2016-3714）、exiftool 特制字段（CVE-2021-22204）、字体/压缩炸弹（解压 42.zip）——上传面无回显也可达（对 C5）。
B8 `.htaccess`/`web.config` 覆盖改解析映射——扩展名白名单不含它们但覆盖即改解析规则。
B9 SVG 存储型 XSS：web 可达 + `Content-Type: image/svg+xml` inline 回吐即执行脚本。
B10 ZIP 条目穿越（Zip Slip）——解压场景下条目名落盘穿越（转 path-traversal 卡 B9）。
B11 表外家族：busboy/multiparty（TS）、JAX-RS @FormDataParam、Tornado `self.request.files`、S3 预签名直传回调——v1 模式表未列，靠本清单扩表。

## ⑨ 利用前提与定级阶梯
见页首。Critical 验收：存储路径 web 可达 + 扩展名可解析 + 一次 GET/POST 触发执行的完整证据链；解析二次利用档需指出具体解析器与版本。band:1 与 band:0 的差别：发卡前必须闭合「三层校验（C2）/存储名（C3）/路径可达性（C4）/解析二次利用（C5）」四问——只凭"存在上传接口"不足以立卡。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 仅本地受信目录存储且回读链无 OBS（无解析/执行消费）→ 降 medium 以下

## ⑩ 根因修复
服务端生成存储名（UUID）+ 扩展名白名单映射（不取客户端段）；三层校验全开且扩展名比较先归一化；存储隔离到非 web 目录或私有桶，下载经鉴权控制器流式回吐并强制 Content-Type；解析管线最小化（ImageMagick policy.xml 禁 MVG/MSL/EPHEMERAL、exiftool 升级、解压逐条目 canonical 校验）；临时名 + 原子 rename 消竞态；大小/数量配额；lint 门禁禁止 originalFilename 直落盘。

## ⑪ 跨边界提示
Egress 侧文件名入库后由下载/删除端点回读（二阶，转 path-traversal）；对象存储直传 + 回调把可控存储名带回服务端；CDN/静态镜像把"非 web 目录"假设打破（回吐面外移）；多实例共享卷使竞态窗口跨节点（C6 的并发面扩大）。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 12/22/6、python 9/13/5、ts 9/12/4
`fixtures/enum/file-upload/{lang}/manifest.tsv`（java 达标集：正例≥10/硬负例≥20/噪音≥5；ts/python 起步集——见 classes/fixture-spec.md 三类语义；manifest 含出处列必填）。
