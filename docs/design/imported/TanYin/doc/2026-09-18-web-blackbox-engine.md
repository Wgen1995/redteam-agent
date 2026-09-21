# web-blackbox 引擎详细设计（B3 前置设计对齐）
> 定位：探隐总控的首个 SKILL 型引擎——Web 黑盒渗透方法论的操作化。
> 权威关系：本文档是 spec §5.2 web-blackbox 行的**引擎级展开**（spec 保留契约级定义，本文档管引擎内部）；冲突时以 spec 为准。
> 方法论来源：CNPEN 斗象项目实战（82 漏洞：黑盒 31+白盒 51）——`C:\Users\c00hwqn\Documents\CNPEN-综合漏洞管理平台-斗象\`（测试全景图/思路复盘/渗透测试记录/31 份黑盒漏洞单）。
> 设计日期：2026-09-18。
## 0. 一句话定位
web-blackbox 是一个**方法论骨架 SKILL**（写一次通用），不是手法集合——攻击手法（SQL 注入怎么测/越权怎么验）在 knowledge/concepts/ 技法页里（数据，运行时检索注入）。引擎回答的问题是：**拿到一个 intent 后，Web 黑盒子代理按什么纪律和流程把它执行成一份合规的提交文件**。
## 1. 目录结构
```
engines/web-blackbox/
├── SKILL.md            # 引擎入口（子代理加载的第一文件）：身份+纪律+四段流程骨架+提交契约
├── phases/             # 四段方法论指令（按 intent 类型按需加载，不整包进上下文）
│   ├── recon.md        # ① 侦察测绘段：资产/服务/端口/文档泄露/前端 JS 提取
│   ├── surface.md      # ② 攻击面测绘段：接口清单/参数枚举/认证体系分析/优先级排序
│   ├── test.md         # ③ 矩阵测试段：按技法页执行单格验证（含 payload 构造规范）
│   └── differential.md # ④ 差分举证段：对照组设计/基线±单变量判定/证据打包
├── patterns/           # 提交文件模板（submission schema 的引擎侧样例+反例）
│   ├── submission-ok.md      # 合规提交样例（含 findings/facts/assets/edges 全字段）
│   └── submission-reject.md  # 被打回的反例（缺 repro_command/凭据未占位符化等）
└── MANIFEST.md         # 引擎清单（kind: skill；适用场景；纪律能力声明；加载预算）
```
**加载策略**（对齐 spec §4.4 上下文生命周期）：SKILL.md 恒载（约 2K token）；phases/ 按当前 intent 的类型加载**一段**（recon 类 intent 只载 recon.md，约 1.5K token）；patterns/ 仅在首次提交被打回后加载（纠错学习，约 1K token）。单子代理上下文预算：引擎自身 ≤5K token，其余留给任务描述+技法页+工具输出摘要。
## 2. 执行协议（intent → 提交文件全链路）
```
总控派发（intent 六要素：目标/scope 摘要/待验证任务/facts 摘要/资产 ID/预算份额）
↓
[子代理会话启动] 加载 engines/web-blackbox/SKILL.md（身份+纪律+流程骨架）
↓
[按需加载] 按 intent.kind 加载 phases/ 对应段 + 总控注入的技法页片段（concepts/ 相关页）
↓
[执行] 四段流程（见 §3）——工具经执行通道调用（B17），三重门横切（deny-list/scope-check/rate_limit）
↓
[产物] 原始输出落盘 session/<goal-id>/submissions/<intent-id>/artifacts/（不进上下文）
↓
[结构化] 按 patterns/submission-ok.md 提炼 submission.json（固定 schema）
↓
[返回] 只回一行状态摘要（status:done + counts）——会话销毁，上下文不残留
↓
总控验收（写前拒收校验→next-id 铸造→八表落账——spec §4.3 单写者模式）
```
**intent.kind 与段的映射**：`recon`→recon.md；`surface`→surface.md；`matrix-test`→test.md+differential.md；`deep-dive`（发现后深挖，如注入利用性验证）→test.md。映射写在 SKILL.md 的流程骨架里，子代理机械跟随。
## 3. 四段方法论（CNPEN 实战提炼的操作化）
### 3.1 ① 侦察测绘段（recon.md）
**做什么**：从已知入口（域名/IP/端口）建立资产与服务清单。
**操作序列**（每步带 CNPEN 实战依据）：
1. 全端口扫描 `nmap -Pn -sS -p- --open --min-rate 5000`（非标准端口常藏管理后台/微服务——CNPEN 8280/9443/10060 全是 -p- 才发现的）
2. 服务识别 `-sV -sC -O`：端口→「这是什么」；**证书 O 字段=厂商自研组件金线索**（9443 证书 O=TopHant → 厂商内部工具，疏于防护概率高）；HTTP 标题+错误响应格式区分后端框架
3. 网络可达性验证：探测本机/跳板机对目标的可达差异（ACL 判断）——**环境约束识别本身是能力**（CNPEN 因 IPS 杀反弹 shell 改人工贴结果模式）
4. 每个发现落 assets.tsv（经总控验收）+ facts（服务指纹）
**纪律**：只读操作（L0 视角）；nmap 速率受 goal 级 rate_limit 约束；界外资产 scope-check 标记不深挖。
### 3.2 ② 攻击面测绘段（surface.md）
**做什么**：从服务清单建立**接口级攻击面地图**。
**操作序列**：
1. 敏感路径批量探测：Java 服务标配泄露点 Swagger（/doc.html、/swagger-resources、/v2/api-docs?group=）/Actuator/Druid——**文档泄露是攻击面地图，比盲测效率高一个量级**（CNPEN 漏洞#1 直接拿到 28 接口清单）
2. 框架元接口挖掘：文档发现机制本身常被遗忘在鉴权外（swagger-resources 返回文档源列表）；**接口返回空/错误≠防护到位，可能是参数不对**（中文 group 参数 URL 编码后才拿到）
3. 前端 JS 分析：**前端 JS 是 API 的说明书**——`/api/` + method 正则提取接口清单（CNPEN 从 15 个业务 JS 提取 134 个写接口）；GraphQL 三板斧：内省→字段建议→前端 JS 提取查询
4. 认证体系还原：抓包还原 SSO/OAuth2/token 链路（授权码模式+state 防 CSRF=设计正常，记录为负结果 fact）
5. 优先级排序：按「漏洞概率×影响」排攻击面（微服务直连>内部工具>有网关主 API——**核心假设：网关统一鉴权+微服务端口直接暴露=直连绕过网关**，CNPEN 8280 证实）
6. 产出落 facts（接口清单/参数结构/认证链路）+ assets（新发现端点）
**纪律**：探测用 GET/空 body 优先（报错信息是免费的需求文档——字段名/格式要求都在里面）；批量探测受 rate_limit。
### 3.3 ③ 矩阵测试段（test.md）
**做什么**：按总控派发的矩阵格（attack_surface×vuln_class）执行技法页验证。
**操作序列**：
1. 读技法页（总控注入的 concepts/ 片段）：适用条件/工具与参数/判定标准
2. payload 构造：按技法页规范+目标上下文（认证 Cookie 用 `{{vault:cred-N}}` 占位符引用，不落明文）
3. 执行：工具经执行通道（curl/Playwright/Burp POC 导出）；**先合法后恶意**（先用合法文件走通流程再测绕过——否则分不清「格式错误」还是「被 WAF 拦」）
4. 判定（**发现→验证→定论三步走**）：
- 状态码会骗人——**看内容类型+响应体**（SPA fallback 对未知路径返 200+text/html≠Actuator 暴露；真实 Actuator 返 application/json）
- **errorCode 语义分析比 HTTP 状态码可靠**（200+errorCode:00000=业务成功；200+00500=请求已进业务逻辑层——都证明无鉴权；401 才是有鉴权）
- **发现≠定级**：注入发现后必须深挖可利用性（CNPEN #7 SQL 报错回显初判高危→ORM 标识符包裹逃逸失败→降级中危）——深挖结论写进 finding 的 confidence 依据
5. 产出：finding（含 repro_command+证据引用）或 fact（负结果：防护有效）——**负结果同样入账**（回归测试基线+差分举证的对照组素材）
**纪律**：测试克制——目标是验证漏洞存在，不是真传 webshell（CNPEN 文件上传测试：恶意扩展名/路径穿越验证后即停）；破坏性 payload 只取证不执行（L3 视角一刀切）。
### 3.4 ④ 差分举证段（differential.md）
**做什么**：给 finding 配合规证据组（spec A12 的引擎侧落地）。
**操作序列**：
1. **对照组设计**：证明「防护本来在别处生效」——同机其他服务的鉴权正常响应（CNPEN #3：8080 网关对未认证返回「未登录」=原校验举证，8280 无鉴权=实验组，两者共享 pair_group）
2. **基线±单变量**：实验组与对照组请求只差一个变量（目标端口/参数值）；同请求基线重复 2 次确认稳定（非偶发）
3. 证据打包：原始请求/响应全文落 artifacts/（双哈希：raw+normalized——归一化去 nonce/时间戳）；POC 写成**第三方可跑**的 curl/Burp 格式（凭据占位符化；Content-Length 精确值标注——CNPEN 漏洞单格式）
4. 提交文件里 findings[].evidence_refs 指向 artifacts 路径+pair_group 标注
**判定规则**（写入引擎契约的机械规则）：实验组与对照组响应差异仅在单变量维度→差异归因成立；响应不稳定（同请求两次结果不同）→标记 unstable，confidence 降一级。
## 4. 上下文预算管理（单子代理）
| 内容 | 预算 | 控制 |
|---|---|---|
| 引擎 SKILL.md | ≤2K token | 恒载，写死 |
| phases/ 单段 | ≤1.5K token | 按 intent.kind 加载一段 |
| 技法页片段 | ≤2K token | 总控注入时截断（只给适用条件+工具参数+判定标准，不给全文） |
| 任务描述+facts 摘要 | ≤1K token | 总控派发时控制（§4.3 六要素） |
| 工具输出 | **0 进上下文** | 原始输出直落 artifacts/；子代理只读结构化摘要（如「200+errorCode:00000+2KB」级别的行级判定） |
| 提交文件 | ≤3K token | schema 定长；超限内容进盘（submissions/ 文件），摘要行返回 |
**为什么工具输出零进上下文**：①敌意内容困在文件里（注入遏制，spec §7）②上下文是燃料也是毒药（PRINCIPLES 摘要纪律）③判定只需要行级结论不需要全文。
## 5. 失败语义落地（spec §5.1 kind: skill 的引擎侧细化）
| 失败类型 | 表现 | 引擎侧处理 | 总控侧处理 |
|---|---|---|---|
| **格式漂移** | 提交文件 schema 校验失败 | 首次打回后加载 patterns/submission-reject.md 对照纠错，重写一次 | 二次仍失败→intent 转 failed（附错误详情），不无限重试 |
| **上下文耗尽** | 子代理会话接近上限 | 立即停止执行，把已完成部分写成部分提交（status:partial+已完成项+未完成清单） | 拆分 intent 为多个子 intent 重新派发 |
| **超时** | 回合预算耗尽 | 同 partial 处理 | 视预算决定重派或转 blocked |
| **环境受阻** | 目标不可达/账号被禁/IPS 阻断 | 记录受阻原因（fact）+**不阻塞**——报告可测面，受阻项显式留痕 | intent 转 blocked 附原因（不可自动复活，须人工） |
| **工具失败** | 命令非零退出 | 重试 1 次（指数退避）；仍失败记 fact（工具不可用+错误摘要） | 换工具路径（技法页备选）或转 blocked |
**CNPEN 依据**：受阻处理三步（记录原因/报障/不阻塞转向无需该依赖的测试面）+「识别环境约束选择可行作业模式」本身是渗透能力。
## 6. 与总控/知识库的接口
**输入**（总控派发时注入）：intent 六要素+技法页片段+相关 facts 摘要+可引用资产 ID+预算份额。
**输出**（提交文件 schema，spec §5.1 定死）：findings[title/confidence/impact/reproducible_steps/evidence_refs/location]+facts[]+assets[]+edges[]——**引擎不直接写账本**，总控验收后统一落账。
**知识库读**：技法页由总控注入（引擎不自己检索——检索是总控的风暴职责，引擎只执行）；实体页 last_verified 由总控在验收时更新。
**差分判定规则**：本引擎契约（MANIFEST.md）声明「同请求基线±单变量+errorCode 语义分析+内容类型验证」三条——总控 lint 降级判定（N≥2 独立反证）依赖此声明。
## 7. CNPEN 素材 → 引擎/知识库的映射（B5 ingest 的输入清单）
| CNPEN 素材 | 去向 | 形态 |
|---|---|---|
| 测试全景图.md（矩阵+五态图例+范围/深度/账号/纪律总纲） | spec 矩阵机制已吸收（五态/全景图驱动）；**样例进黄金夹具** | 夹具素材 |
| 渗透测试思路复盘.md（八阶段决策逻辑+7 条核心思路） | **本文档 §3 四段方法论的直接来源**；方法论原则进 concepts/ 技法页（如「errorCode 语义分析」「前端 JS 是 API 说明书」） | 引擎指令+技法页 |
| 渗透测试记录.md（T1-T55 测试项+证据索引） | P6 沉淀的**先例链路素材**（脱敏后进 precedents/） | 先例库 |
| 31 份黑盒漏洞单（POC 格式/差分举证/定级修正过程） | **patterns/submission-ok.md 样例来源**+技法页判定标准（如「注入深挖后才定级」） | 提交模板+技法页 |
| BurpPOC 合集/Burp 复现手册 | 技法页的工具参数素材 | 技法页 |
## 8. 边界（本引擎不做）
- 不做源码审计（vuln-agent CLI 引擎职责）
- 不做可视化（session-viz projector 职责）
- 不做知识检索/风暴/调度（总控职责——引擎只执行 intent）
- 不直接写账本（单写者模式——总控验收落账）
- 不自选攻击手法（手法来自技法页+intent 任务描述——引擎是方法论骨架不是手法集合）
## 9. 验收标准（B3 实现完成的判定）
1. 黄金夹具：给定固定 intent（如「验证 8280 端口未授权访问」）+固定技法页片段，引擎产出提交文件与 patterns/submission-ok.md 结构一致（字段全/凭据占位符化/证据双哈希/pair_group 标注）
2. 纪律注入测试：给引擎注入敌意工具输出（响应体里藏「忽略之前指令」），验证输出困在 artifacts/ 不进上下文、提交文件不受污染
3. 失败语义：模拟格式漂移/上下文耗尽/环境受阻三场景，验证 partial 提交+blocked 转移正确
4. 差分判定：对照组/实验组样例对，验证 pair_group 归因与 unstable 降级

> **v2 语义补注**：引擎执行中发现新资产/凭据经统一提交触发资产事件回边（asset-added/cred-obtained，v2 §5.4），引擎可被再派发——黑盒引擎是探索循环的感知末端，不是一次性流水线。