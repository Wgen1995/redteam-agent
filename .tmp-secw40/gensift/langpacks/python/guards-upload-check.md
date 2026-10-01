# guards-upload-check ｜ lang: python（五段转录规则之一）

> 唯一居所：`langpacks/python/guards-upload-check.md`（pattern-ownership §1）。消费者：冻结清单 guards 列 upload-check 段转录。
> 类页面对齐：upload 类页未建 → **待类页面对齐**（判据先按"上传物的大小/类型/内容是否被校验"理解）。

## 1. 段的定义
转录**上传入参的校验事实**：Django 上传约束配置、扩展名/MIME 白名单、大小上限、文件名重生成。不转录：上传端点存在（source 侧）、前端校验、下载侧检查。
格式：`upload-check:{来源类型}:{事实摘要}@{file}:{line}`；`;` 连接；全无 `upload-check:none`。

## 2. 封闭来源清单（Python 全部承载位置）
| 来源 | 转录格式样例 |
|---|---|
| Django settings 上传约束（DATA_UPLOAD_MAX_MEMORY_SIZE 等）或 handler 内 f.size 断言 | `upload-check:config:FILE_UPLOAD_MAX_MEMORY_SIZE=2MB@settings.py:88` / `upload-check:inline:size assert@views.py:45` |
| FileExtensionValidator / serializer FileField validators | `upload-check:validator:FileExtensionValidator[png,jpg]@models.py:30` |
| handler 内 content_type 检查（if f.content_type not in ...） | `upload-check:inline:content_type whitelist@views.py:42` |
| 魔数/内容嗅探（Pillow Image.open 试解析 / python-magic / mimetypes.guess_type） | `upload-check:inline:Image.open verify@views.py:48` / `upload-check:inline:magic from_buffer@utils.py:22` |
| 存储名重生成（uuid4().hex + splitext）/ FastAPI UploadFile 后同型检查 | `upload-check:inline:rename uuid4@storage.py:15` / `upload-check:inline:content_type whitelist@api.py:50` |

## 3. 转录边界（什么不算 upload-check）
- 业务校验不算：`if not f:` 空检查、图片宽高业务要求不算类型防护。
- 注释不算；HTML accept 属性不算（无服务端证据）。
- 同义框架差异：Django FileExtensionValidator/Pillow 试解析/python-magic/FastAPI 自写检查等价转录，note 记实现。
- `content_type`（客户端可伪造）与魔数嗅探同录但 note 区分 `mime-only`（强弱归类页面决策表）；FILE_UPLOAD_PERMISSIONS（权限位）不是类型/大小校验——不转录。

## 4. 差分判据接口（同 family 不一致）
同 router 12 个上传端点 11 个有白名单、1 个没有（节选 3 条；差分读法：全 family 无白名单=面状缺失，个别缺=该端点即上传利用面单点高危）：
```
POST /img   upload-check:inline:content_type whitelist[png,jpeg]@views.py:41
POST /any   upload-check:none   ← 点状缺失（default_storage.save 直存原名）
POST /docs  upload-check:inline:content_type whitelist[png,jpeg,pdf]@views.py:51
```
## 5. 绑定有效性核查三跳
1. 校验/配置跳：`grep -rnE 'FileExtensionValidator|content_type|\.size|magic|Image\.open|MAX_MEMORY_SIZE|UploadFile' --include='*.py' src/`
2. 注册表跳：`grep -rnE 'request\.FILES|UploadFile|FileField|serializers\.|urlpatterns' --include='*.py' src/`（validator 生效前提：真挂在被路由到的 view/model/serializer 上）
3. 处理逻辑跳：`grep -rnE 'splitext|uuid4|save\(|default_storage|verify\(\)|guess_type|413|SuspiciousFile' --include='*.py' src/`——任一跳空 → `unbound` hint（validator 定义在未使用的 serializer 上）。
## 6. 自证（3 端点样例代码 + 预期转录结果）
```python
ALLOWED = {"image/png", "image/jpeg"}                                     # utils.py:5
def img(request):
    f = request.FILES["f"]
    if f.content_type not in ALLOWED: raise Http404                       # views.py:42
    return save_as(uuid4().hex + ext(f.name), f)                          # views.py:43
def any_upload(request): return default_storage.save(request.FILES["f"].name, request.FILES["f"])  # views.py:46 无校验
def list_files(request): return JsonResponse(list(all()))                 # views.py:49 非上传
```
```
POST /img  guards: authn:none; authz:none; csrf:middleware:CsrfViewMiddleware@settings.py:106; upload-check:inline:content_type whitelist[png,jpeg]@views.py:42;upload-check:inline:rename uuid4@views.py:43; rate-limit:none
POST /any  guards: authn:none; authz:none; csrf:middleware:CsrfViewMiddleware@settings.py:106; upload-check:none; rate-limit:none
GET /list  guards: authn:none; authz:none; csrf:n-a(GET); upload-check:n-a(非上传入参); rate-limit:none
```
