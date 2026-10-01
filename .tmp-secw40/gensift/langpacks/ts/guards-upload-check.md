# guards-upload-check ｜ lang: ts（五段转录规则之一）

> 唯一居所：`langpacks/ts/guards-upload-check.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 upload-check 段转录。
> 类页面对齐：upload 类页未建 → **待类页面对齐**（判据先按"上传物的大小/类型/内容是否被校验"理解）。

## 1. 段的定义
转录**上传入参的校验事实**：multer fileFilter/limits、类型白名单、大小上限、文件名重生成。不转录：上传端点的存在（source 侧）、前端校验、下载侧检查。
格式：`upload-check:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `upload-check:none`。

## 2. 封闭来源清单（TS 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| multer fileFilter（白名单拒绝） | `upload-check:multer:fileFilter mimetype[images]@upload.ts:18` |
| multer limits（fileSize/files） | `upload-check:multer:limits.fileSize=2MB@upload.ts:19` |
| 路由级 upload.single/array + filter 组合 / Nest FileInterceptor+options | `upload-check:multer:FileInterceptor limits=5MB@file.controller.ts:30` |
| handler 内显式 MIME 检查（mimetype 白名单 if throw） | `upload-check:inline:mimetype whitelist[png,jpg]@file.controller.ts:44` |
| 扩展名检查（path.extname + 白名单） | `upload-check:inline:ext whitelist@file.controller.ts:46` |
| 魔数/内容嗅探（file-type 包 buffer 检测） | `upload-check:inline:fileType sniff@scan.ts:25` |
| 存储名重生成（diskStorage filename 用 uuid）/ busboy/formidable 校验 | `upload-check:multer:rename uuid@upload.ts:12` / `upload-check:mw:busboy limits@upload.ts:33` |

## 3. 转录边界（什么不算 upload-check）
- 业务校验不算：`if (!req.file)` 空检查、业务宽高要求不算类型防护。
- 注释不算；HTML `accept=".png"` 前端属性不算（无服务端证据）。
- 同义框架差异：multer/busboy/formidable/@nestjs/platform-express 等价转录，note 记实现。
- multipart 解析器本身不算校验——只有 limits/fileFilter 才算；`mimetype` 检查（客户端可伪造）与魔数嗅探同录但 note 区分 `mime-only`（强弱归类页面决策表）。

## 4. 差分判据接口（同 family 不一致）
同 controller 12 个上传端点 11 个有 fileFilter、1 个裸 multer（节选 3 条；差分读法：全 family 无 filter=面状缺失，个别缺=该端点即上传利用面单点高危）：
```
POST /img   upload-check:multer:fileFilter mimetype[images]@routes.ts:39
POST /any   upload-check:none   ← 点状缺失（裸 upload.single）
POST /docs  upload-check:multer:fileFilter mimetype[images]@routes.ts:41
```
## 5. 绑定有效性核查三跳
1. 配置跳：`grep -rnE 'multer|fileFilter|limits|fileSize|FileInterceptor|busboy|formidable' --include='*.ts' src/`
2. 注册表跳：`grep -rnE "upload\.(single|array|fields)|app\.use\(upload|Interceptors\(" --include='*.ts' src/`（filter 生效前提：带 options 的 multer 实例真挂在该路由上）
3. 处理逻辑跳：`grep -rnE 'mimetype|originalname|extname|fileTypeFromBuffer|413|PayloadTooLarge' --include='*.ts' src/`——任一跳空 → `unbound` hint（定义了 filter 变量但路由用的是裸 upload）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```ts
const up = multer({ storage: uuidStorage(), limits: { fileSize: 2 * 1024 * 1024 },        // upload.ts:10-11
  fileFilter: (req, f, cb) => cb(null, /png|jpg/.test(f.mimetype)) });                      // upload.ts:12
router.post('/img', up.single('f'), img);      // routes.ts:20
router.post('/any', multer().single('f'), any);// routes.ts:21 无校验
router.get('/list', list);                     // routes.ts:22
```
```
POST /img  guards: authn:none; authz:none; csrf:none; upload-check:multer:fileFilter mimetype[png|jpg]@upload.ts:12;upload-check:multer:limits.fileSize=2MB@upload.ts:11;upload-check:multer:rename uuid@upload.ts:10; rate-limit:none
POST /any  guards: authn:none; authz:none; csrf:none; upload-check:none; rate-limit:none
GET /list  guards: authn:none; authz:none; csrf:n-a(GET); upload-check:n-a(非上传入参); rate-limit:none
```
