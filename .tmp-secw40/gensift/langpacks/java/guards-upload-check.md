# guards-upload-check ｜ lang: java（五段转录规则之一）

> 唯一居所：`langpacks/java/guards-upload-check.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 upload-check 段转录。
> 类页面对齐：upload 类页未建 → **待类页面对齐**（判据先按"上传物的大小/类型/内容是否被校验"理解）。

## 1. 段的定义
转录**文件上传入参的校验事实**：扩展名/MIME/魔数白名单、大小上限、存储文件名重生成（路径穿越归 path-traversal 类，本段 note 最多）。不转录：上传端点的存在（source 侧）、仅前端校验、下载侧校验。
格式：`upload-check:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `upload-check:none`。

## 2. 封闭来源清单（Java 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| MultipartFile 入参后 MIME 检查（getContentType/probeContentType 白名单） | `upload-check:inline:contentType in {png,jpg}@FileApi.java:42` |
| 扩展名/文件名检查（getOriginalFilename + 后缀白名单） | `upload-check:inline:ext whitelist[png,jpeg]@FileApi.java:45` |
| 大小限制（multipart.max-file-size 配置或 length() 断言） | `upload-check:config:max-file-size=2MB@application.yml:24` |
| 魔数/内容嗅探（ImageIO.read 试解析、Tika detect） | `upload-check:inline:tika detect@ScanSvc.java:30` |
| ServletRegistrationBean 的 multipart 配置 / Commons FileUpload setFileSizeMax | `upload-check:config:MultipartConfigElement@WebConfig.java:28` |
| Bean Validation @Size 等在 MultipartFile 参数 | `upload-check:anno:@Size(max=...)@FileApi.java:38` |
| 存储前重命名（UUID 新名/去原始名） | `upload-check:inline:rename uuid@StoreSvc.java:52` |

## 3. 转录边界（什么不算 upload-check）
- 业务校验不算：`if (file == null)` 空检查、图片业务属性（宽高比）不算类型防护。
- 注释不算；仅 JS/前端 accept 属性不算（无服务端证据）。
- 同义框架差异：Spring MultipartFile/Servlet 3.0 Part/Commons FileUpload 等价按各自形态转录。
- `Files.probeContentType` 与手工后缀判断同档（都可伪造，强弱归类页面决策表）；病毒扫描异步化（先存后扫）转录但 note `async`（窗口事实留给 Analyzer）。

## 4. 差分判据接口（同 family 不一致）
同 controller 12 个上传端点 11 个有类型白名单、1 个没有（节选 3 条；差分读法：全 family 无校验=面状缺失，个别缺=该端点即上传利用面单点高危）：
```
POST /avatar       upload-check:inline:contentType in {png,jpg}@FileApi.java:42
POST /attachments  upload-check:none   ← 点状缺失
POST /docs/upload  upload-check:inline:contentType in {png,jpg,pdf}@FileApi.java:70
```
## 5. 绑定有效性核查三跳
1. 配置跳：`grep -rnE 'MultipartFile|getContentType|getOriginalFilename|probeContentType|max-file-size|sizeMax' --include='*.java' --include='*.yml' src/`
2. 注册表跳：`grep -rnE 'MultipartConfigElement|multipart-config|@RequestPart|StandardServletMultipartResolver' --include='*.java' --include='*.xml' src/`（配置生效前提：multipart resolver 被注册）
3. 处理逻辑跳：`grep -rnE 'ImageIO\.read|Tika|magic|startsWith\("image|endsWith\("\.|length\(\)' --include='*.java' src/`——任一跳空 → `unbound` hint（yml 有 max-file-size 但 resolver 未启用）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```java
@RestController public class FileApi { @PostMapping("/img") public String img(@RequestParam MultipartFile f){   // L37-38
    if (!List.of("png","jpg").contains(ext(f.getOriginalFilename()))) throw new IllegalArgumentException();     // L39
    return store.rename(UUID.randomUUID()); }                                                                  // L40
  @PostMapping("/any") public String any(@RequestParam MultipartFile f){ return store(f); }                    // L43 无校验
  @GetMapping("/list") public Object list(){ return store.all(); } }                                           // L46 非上传
```
```
POST /img  guards: authn:none; authz:none; csrf:none; upload-check:inline:ext whitelist[png,jpg]@FileApi.java:39;upload-check:inline:rename uuid@FileApi.java:40; rate-limit:none
POST /any  guards: authn:none; authz:none; csrf:none; upload-check:none; rate-limit:none
GET /list  guards: authn:none; authz:none; csrf:n-a(GET); upload-check:n-a(非上传入参); rate-limit:none
```
