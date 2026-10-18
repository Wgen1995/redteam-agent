# cmd-injection ｜ 命令注入（CWE-78）

> band: 0 ｜ 模式表: `patterns/cmd-injection-{java,ts,python}.pattern` ｜ fixture: `fixtures/enum/cmd-injection/`
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 定级阶梯: 可控输入 + shell 解释通道 + 结果可观测（回显/OOB/持久化）→ Critical（即 RCE）；盲信道可达（无回显但时间差/退出码/DNS 反连）→ High；仅固定二进制枚举参数注入（无 shell 元字符语义、参数白名单成立）→ 降 Medium（前提引文）

## ① 定义与危害
用户可控输入未经参数化直接拼入操作系统命令行，攻击者借 shell 元字符（`;` `|` `&&` 反引号 `$()`）改变命令语义——从固定工具调用升级为任意命令执行（RCE），直接通向数据外带、凭据读取、持久化后门与横向移动。

## ② Source
HTTP 参数/路径/头部/_body_、消息体（external_message）、**存储回读（persisted_read——二阶注入：上传文件名/日志字段/DB 字段回读后拼入命令）**、可被 API 写入的命令模板配置项。回读值默认 unknown 可控性，禁止在 VERIFY 中当"不可控"反证。

## ③ Sink 模式表指针
`patterns/cmd-injection-java.pattern` / `cmd-injection-ts.pattern` / `cmd-injection-python.pattern`（机器直读，逐行一条，不并串）。

## ④ Propagator
字符串拼接（`+`/模板串/f-string/`format`）、StringBuilder.append 链、`String.join`/`" ".join`、ProcessBuilder 的 `.command()` 链、模板引擎渲染产物直接作命令行。跨字段保守传播。

## ⑤ Sanitizer（决策表三值）
参数数组形式（`exec(String[])`/ProcessBuilder 数组/spawn 数组无 `shell:true`/subprocess list 形态——每元素一个独立实参，不经 shell 元字符解释）→ **强**（仅当元素本身无拼接且无 `sh -c` 包装）；命令与子命令/选项白名单枚举映射 → **强**；黑名单过滤/引号转义（缺 `${IFS}`、`$()`、编码变体；escapeshellarg 与目标 shell 方言不符）→ **弱**；`if(strict)` 才启用 → **上下文条件（只产 hint，禁 kills）**。**多段净化看全部；数组形式里元素内部拼接/`sh -c` 包装是"净化与载荷形态不匹配"。**

## ⑥ 判定流程（编号条目）
C1 输入是否外部可控（参数/消息/回读/配置）？｜引用:入口签名与取参行｜推翻:实参为编译期常量｜反向:文件名/日志字段等存储回读值拼入
C2 命令文本是否含拼接变量或模板插值？｜引用:命令构造行±3行｜推翻:命令与参数全字面量｜反向:builder/command() 链尾 join 的间接拼接
C3 执行通道是否经 shell 解释（exec 单串/execSync/spawn shell:true/os.system/`sh -c` 包装）？｜引用:sink 调用行形态｜推翻:参数数组形式且各元素独立无拼接｜反向:数组形如 ["sh","-c",拼接串] 的伪参数化
C4 净化是否消除 shell 载荷形态（决策表查值）？｜引用:净化调用行+其叶子实现｜推翻:白名单枚举命中且映射闭合｜反向:黑名单缺 IFS/引号拆分/编码变体
C5 入口可达且鉴权不拦截？｜引用:路由注解/拦截器/中间件配置｜推翻:内网-only 且有边界证据｜反向:默认放行/运维端点复用业务命令
C6 执行结果可观测（回显/stdout 管道/退出码/时间差/OOB）？｜引用:输出读取行（getInputStream/stdout 回调/check_output）｜推翻:输出丢弃且无时间差｜反向:反连信道（DNS/HTTP）可用
C7 二阶形态：payload 是否经存储（文件名/日志/DB 字段）回读后再进命令？｜引用:回读点与拼接点两处行号｜推翻:回读值仅作展示/长度校验｜反向:回读值直接进入命令串
C8 运行身份与解析环境是否放大影响（root 容器/PATH 可写/命令名走相对路径）？｜引用:部署清单/入口用户/PATH 构造行｜推翻:非特权用户+只读 FS+绝对路径命令｜反向:以 root 运行且命令名经 PATH 解析

## ⑦ 常见误报（FP 卡，只增+deprecate 留痕）
FP-1 ProcessBuilder 数组形式（每元素独立实参，不经 shell）——安全形态，除非数组元素内部含拼接或被 `sh -c` 包装（需 OBS 链证据，见 C3 反向）。
FP-2 TS `.exec(` 是 RegExp 方法、业务 `execute()`/Promise executor——CI-T03 已用显式边界排除点前缀；家族标记命中的需 OBS 排除。
FP-3 Python `model.eval()`/`df.eval()`/`ast.literal_eval`——点前缀与前缀词形态，非动态执行（CI-P12 边界证据）。
FP-4 `execFile`/spawn 数组形式（不走 shell）与 `subprocess` list 形态——同 FP-1，枚举层命中是设计属性。
FP-5 固定命令 + 白名单枚举参数（如 `git` 子命令映射表）——净化决策表"强"档，需映射闭合证据。

## ⑧ 常见漏报与绕过（bypass 提示单——去尝试，不是去阅读）
B1 空格绕过：`${IFS}`、`$IFS$9`、重定向 `<` 替分隔（`cat</etc/passwd`）、tab（`%09`）。
B2 关键字黑名单绕过：引号拆分 `ca""t`、反斜杠插入 `c\at`、未过滤的 `|`/`&&`/反引号/`$()`。
B3 白名单缺陷：正则锚缺失/子串匹配/大小写——`tar;curl sh` 过 `^(tar|zip)`。
B4 伪参数化：`new String[]{"sh","-c",user}` 数组形式但末元素整体经 shell 二次解释。
B5 编码与中间解释器：base64 现场解码、`bash -c`/`python -c`/`find -exec`/`awk system()` 间接执行。
B6 二阶与路径劫持：payload 经存储回读再拼接；命令名经 PATH/相对路径解析可控。

## ⑨ 利用前提与定级阶梯
见页首；Critical 验收：可演示任意命令执行（交互式 shell/回显外带/OOB 反连），专业审查者无需长篇推测即可接受利用路径。
降级反例（B-109——出现下列形态时不应保持 high/critical，降级须引文）: 实参全字面常量（B-053 常量实参信号命中）或命令仅内部固定白名单分发（引文）→ 降 low/info

## ⑩ 根因修复
一律参数数组形式执行固定命令（命令名用绝对路径）；子命令/选项走白名单映射；禁止 `sh -c` 包装用户输入；`child_process.exec`/`os.system`/`shell=True`/`Runtime.exec(单串)` 形态进 CI lint 门禁。

## ⑪ 跨边界提示
Egress 侧拼接好的命令经 SSH/消息队列下发到执行节点（Agent 型架构：注入点与执行点分离，落账时挂跨模块证据）；Ingress 侧上传文件名/头部/回调 URL 直接进命令；CI/CD 管道变量经构建脚本 shell 二次展开（`${VAR}` 注入）。

## ⑫ fixture 指针
实际档位（D-066/D-067——以 manifest 对账为准，达标集 neg≥20 为目标口径，缺口如实披露）: java 12/21/5、python 11/10/5、ts 10/10/4
`fixtures/enum/cmd-injection/{lang}/manifest.tsv`（java 正例≥10/硬负例≥20/噪音≥5；ts、python 起步集 正例≥6/硬负例≥8/噪音≥3——见 classes/fixture-spec.md 三类语义）。
