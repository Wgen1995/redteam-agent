# 端点字典 v2（靶场扩编 20→50 弹药·二级路径与认证态策略）

> 来源：靶场首战漏检归因（HANDOFF 705-717 节，合法输入）+GT 键口径教训。服务对象：①矩阵词表增补（matrix-init TYPE_VOCAB_CLASSES 消费面）②扩编种子设计（50 靶端点面）③P0 认证态检查单。
> 纪律：本字典=方法论面（不含任何靶场 marker/答案字面量——那是 GT 域，禁读纪律不破）。

## 一、二级路径增补（首战 7 漏检中 6 项的共同根因：120+ 词表无这些键）

### 1.1 交互面二级路径（业务流后端点）
| 路径模式 | 探测手法 | 关联漏洞类 |
|---|---|---|
| /comment、/reply、/feedback | POST 参数化注入探针（回显差分） | XSS/注入 |
| /preview、/render、/template | SSRF 探针（URL 参数→行为差分：响应码/时延/回显） | SSRF/模板注入 |
| /import、/upload、/export | multipart 边界+类型混淆 | 反序列化/上传绕过 |
| /unserialize、/deserialize、/decode | 结构化 payload 探针（Java/PHP/Python 形态分型） | 反序列化 |
| /debug/env、/debug/vars、/actuator/env、/metrics、/.env、/info | GET 直取（信息暴露类高频） | 信息暴露 |
| /cors-debug、/cors、/origin | Origin 变体矩阵（evil.com/null/子域） | CORS 配置错误 |
| /admin、/manage、/console | 直取+默认凭据对 | 越权/默认凭据 |
| /api/v2/*、/internal/*、/private/* | 版本面/内部面前置词穷举 | 版本暴露旧接口 |

### 1.2 两段式路径探测（首战建议 2）
一级命中后强制二段：/api/<资源>/<id>/<动作>、/<资源>/<id>/edit、/debug/<一级命中>/env——词典消费=matrix 行铸造时 surface 列带二级段。

## 二、认证态获取策略（P0 检查单·首战 5 不可达根因）

1. 弱口令清单：admin/admin、admin/password、user/123456、test/test、guest/guest（靶场口径高频）——login 面 403 不代表排除（weakpass-01 教训：固定 403 无泄露≠不可爆破，改行为差分：成功/失败响应字节差+时延差）。
2. 默认凭据面：注册通道开放判定（/register、/signup 200 即登记新凭据行 add-cred）。
3. 会话升级链：匿名可达端点中找 token 泄露（/debug/env 类）→凭据链推导（CRED 行+scope_asset 绑定）。
4. 每获得凭据=P0 矩阵重映射（触发器 ①/② 联动：资产/凭据落账即子矩阵行）。

## 三、GT 键口径（battle-1 T16 已修，扩编种子必守）

种子端点键=host:port 全量规范形（svc DNS 名+端口），scorer _norm_endpoint 归一（host_aliases 传参）；新种子设计时 GT 键与资产命名同源（add-asset value=svc 名:端口）。

## 四、扩编 20→50 面指引

- 现存 8 服务类保持（xss/ssrf/cors/deser/infoleak/weakpass/sqli/idor 各类加密度）。
- 新类候选：文件包含（LFI/RFI）、开放重定向、JWT 弱验、速率限制缺失、GraphQL 内省、XXE、CSRF、路径穿越——每类 2-4 端点，二级路径占比≥40%（对齐本字典一节）。
- 认证态类靶（weakpass 等）必配行为差分通道（非固定回显）。
