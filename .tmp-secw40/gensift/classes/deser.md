# deser ｜ 不安全反序列化（CWE-502）

> band: 0 ｜ 模式表: `patterns/deser-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/deser/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 互斥归属（D-010）: 本类只收「按载荷类型描述符重建对象图」（readObject/autoType/unserialize）；代码/模板文本求值归 code-injection；查询语义改写归 sqli/injection-misc；JNDI lookup 的出网查找点归 ssrf 出网面——本类只在 JNDI 作为 gadget 链一环时记录，不双计。
> 定级阶梯: 可控源 + 无类型白名单 → ≥High；classpath 有已知 gadget（依赖清单 × `langpacks/*/known-gadgets.tsv` 命中）→ Critical；仅资源耗尽/DoS 形态（深嵌套对象图、巨型集合）→ Medium（前提引文）

## ① 定义与危害
用户可控字节流/多态文本进入对象图重建入口（readObject/fromXML/autoType/default typing/unserialize），攻击者借 classpath 上既有类构造 gadget 链达成任意调用（RCE）、JNDI/SSRF 出网或资源耗尽。与"解析"类（JSON.parse/DOM parse/json.loads，见 neg 目录）的分界：**是否按载荷里携带的类型描述符实例化对象**——实例化权在载荷即本类，在服务端固定类型即解析。

## ② Source
HTTP body/cookie/header、消息队列载荷、Redis/Memcached 回读、**存储回读（persisted_read——二阶：上周落库的序列化 blob 本周被 readObject）**、session 恢复流、上传文件路径可控的工件回读。Base64/Hex/URL 编码只改载体不改语义——**编码不是净化**。回读值默认 unknown 可控性，禁止在 VERIFY 中当"不可控"反证。

## ③ Sink 模式表指针
`patterns/deser-java.pattern` / `deser-ts.pattern` / `deser-python.pattern`（机器直读，逐行一条，不并串）。Java 的 `\.readObject\(` 是家族标记：JDK OIS/XMLDecoder/Kryo 同名读点一并兜住，安全/危险由五步法判别；SnakeYAML `new Yaml(` 等未列举家族走 §⑧ B2 扩清单，不进 v1 模式表。

## ④ Propagator
字节流透传：`Base64.decode` / `IOUtils.toByteArray` / `request.getInputStream` / `Buffer.from` / `base64.b64decode` / fs/queue 读出。载荷形态不随透传改变，跨方法/跨服务保守传播；shelve/marshal 常藏在"缓存工具"封装类里，读点离入口三层以上也要追。

## ⑤ Sanitizer（决策表三值）
类型白名单（OIS 子类 resolveClass allowlist + `ValidatingObjectInputStream.accept` ｜ Jackson `PolymorphicTypeValidator` allow ｜ fastjson `autoTypeFilter`+`addAccept` ｜ SnakeYAML `SafeConstructor` ｜ js-yaml `safeLoad`/≥4 默认 schema ｜ PyYAML `SafeLoader`）→ **强**（仅当覆写链闭合、allow 列表不被通配冲开）；黑名单 deny（gadget 包名清单）→ **弱**（gadget 家族增长快于黑名单）；长度/嵌套深度限制、类数配额 → **上下文条件（只产 hint，禁 kills）**；"先验签再反序列化" → 显式挂 `requires_config`（密钥管理失效即整体失效）。**多段净化看全部；"校验过长度"不是类型白名单是形态错配。**

## ⑥ 判定流程（编号条目）
C1 输入来源是否可跨请求控制（body/cookie/header/消息/缓存回读/落库 blob/上传工件）？｜引用:入口签名与取流行｜推翻:流为服务端自产常量（编译期字面/本地只读工件）｜反向:上传文件路径可控的回读
C2 反序列化类型是否有白名单（resolveClass/acceptFilter/PolymorphicTypeValidator/autoTypeFilter/SafeConstructor/safeLoad）？｜引用:白名单声明行+覆写方法体全量｜推翻:显式 allow 列表且覆写链闭合｜反向:仅黑名单 deny 或仅"校验长度/签名"
C3 gadget 家族是否在 classpath？｜引用:依赖清单(pom/package.json/requirements) × `langpacks/*/known-gadgets.tsv` 命中行｜推翻:依赖缺失或版本落在已修区间｜反向:fat-jar/shaded 内嵌未在清单声明
C4 载荷到达读点前是否被阻断（验签/解密门）？｜引用:取流到读点之间调用链｜推翻:验签先于读且密钥不可绕｜反向:Base64/hex 仅编码被当"已净化"
C5 入口可达且鉴权不拦截？｜引用:路由注解/端口暴露(T3/HTTP/RPC)｜推翻:内网-only 且有边界证据｜反向:健康检查/调试端点后藏读点
C6 载荷是否可跨请求重放或持久化（cookie、session blob、队列投毒）？｜引用:载荷存储与回读行｜推翻:一次性流即弃｜反向:缓存键含用户输入
C7 危害是否仅资源耗尽（深嵌套集合/巨型对象图，无调用链 gadget）？｜引用:依赖清单无 gadget 家族+构造形态引文｜推翻:存在 InvokerTransformer 类调用语义证据｜反向:构造仅为巨型集合且 C3 全阴

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 带白名单 resolveClass 的 OIS 子类——D-J01 命中但 C2 反证（noise/ois-resolveclass-whitelist）。
FP-2 固定目标类型读取（readValue(User.class)/parseObject(text,User.class)/fromJson(json,User.class)/plainToInstance）——类型不由载荷决定。
FP-3 `yaml.load(…, Loader=SafeLoader)`、js-yaml ≥4 默认安全 schema——需版本证据（C2/C3）。
FP-4 `serialize(` 写出端与 jQuery `form.serialize()`（URL 编码）——非对象图重建。
FP-5 `defaultReadObject/readFields/readInt` 等流内原语与 `readObject` 方法签名声明——签名相似非读点。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 `@type` 在变量里：`JSON.parseObject(body)` 载荷经请求传入时行内无 `@type` 字面——pattern 只认行内形态，入口扫描兜。
B2 未列举家族：SnakeYAML `new Yaml(`/Kryo/Hessian2/Fst/Kotlinx-Serialization——`\.readObject\(` 兜一部分，其余进 `known-gadgets.tsv` 扩 pattern。
B3 二阶：序列化 blob 落库回读（追 persisted_read，C6）。
B4 自定义 RPC 帧按 magic number 分发到隐藏 OIS——入口不在 HTTP 面。
B5 黑名单 resolveClass 被 gadget 新家族绕过（deny 清单陈旧）。
B6 import 解构后裸调用 `unserialize(…)`——member 形态 pattern 不命中，入口扫描兜。
B7 业务自有"叫 deserialize 的普通方法"——签名不含序列化库类型时非 sink，看签名再报。

## ⑨ 利用前提与定级阶梯（含静态档 payload 形态声明）
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 仅资源耗尽/DoS 形态（深嵌套对象图，无 gadget 链证据）→ 降 medium；类型白名单引文在位 → refuted 方向
**静态档 payload 形态声明（定稿 v1.3 采纳 B#10）**：多跳 gadget 链给不出可复制的序列化字节流——本类 payload 不以字节流表达，以三段表达：① **gadget 类链叙述**（如 Commons-Collections：`LazyMap` 装载 `InvokerTransformer` 链 → `TiedMapEntry.toString`/`AnnotationInvocationHandler` 触发端，逐跳给类名+方法语义）；② **依赖版本证据**（pom/package.json/requirements 声明坐标与版本 ∈ known-gadgets.tsv 已知可利用区间）；③ **classpath 可达性引文**（依赖树展开行/`Class.forName` 实测/启动 classpath 清单）。三段齐 → Critical；缺 ③ → 记 High 并挂 blocked-on-evidence；**禁止以"无法给出序列化字节流"否定可达性**。
**OBSERVE gadget 检查清单（C3 的证据形态，逐项找引文）**：
- Commons-Collections InvokerTransformer 链（CVE-2015-7501 家族：commons-collections ≤3.2.1/4.0，含 TransformingComparator/InstantiateFactory 变体）
- Jackson polymorphic（enableDefaultTyping/activateDefaultTyping 无 allowlist，CVE-2017-7525 家族）
- fastjson autoType（SupportAutoType 显式开、≤1.2.24 默认放行、后续黑白名单逃逸族，CVE-2017-18349）
- SnakeYAML 构造（`new Yaml()` 未配 SafeConstructor，!!javax.script 相关标签族）
定级阶梯：**可控源 + 无类型白名单 ≥ High；classpath 有已知 gadget = Critical；仅 DoS = Medium**。High 验收：专业审查者无需长篇推测即可接受"可控字节流 → 任意类实例化路径"。

## ⑩ 根因修复
载荷不携类型（JSON+DTO/protobuf schema 替代序列化 blob）；必须反序列化处上类型白名单（resolveClass allowlist/PolymorphicTypeValidator/SafeConstructor），禁黑名单；依赖治理：JDK/commons-collections/fastjson/jackson-databind 升级出已知 gadget 区间；JEP 290 serialization filter 全局默认；序列化端点下线。

## ⑪ 跨边界提示
序列化 blob 跨服务/跨缓存透传（写入方与读出方不同服务——**读侧 classpath 决定 gadget 面**，写侧无害不代表链路无害）；消息队列与 session 存储是常见二阶载体；JNDI/JdbcRowSet 类 gadget 把危害外溢成 SSRF/出网（出网证据进 VERIFY 跨边界引文）。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 12/20/6、python 8/10/4、ts 7/10/4
`fixtures/enum/deser/{lang}/manifest.tsv`（java：正例≥10/硬负例≥20/噪音≥5；ts/python 起步集 6/8/3——见 classes/fixture-spec.md 三类语义）。
