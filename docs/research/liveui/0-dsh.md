# dsh（DeepSeek Harness）Web GUI 源码级分析报告（遥控器家族定位 + UI 参照）

> 分析对象：dsh @ `/opt/homebrew/lib/node_modules/@deepseek-ai/dsh`（v0.2.0-rc.2，MIT）
> 分析日期：2026-10-16 · 分析者：探隐委托子代理
> 证据基础：
> ① **npm 安装真身直读**：该目录虽无 apps/ 源码树，但全部功能包以**未压缩可读 esbuild/rolldown bundle** 发布——每个 `#region` 注释还原了原仓路径（`/home/runner/work/deepseek-harness/deepseek-harness/packages/...`），等于拿到了带注释的编译态源码；
> ② **包级 README 双语参考文档**：每个 @deepseek-ai/dsh-* 包自带 package-reference 级 README（行为契约级描述，非营销文档），本报告大量引用；
> ③ **web-frontend dist 产物**：Vite 构建的 shell bundle（index-5SrrfWpU.js 633KB + vendor 740KB）+ 61 个语言包 + 字体；
> ④ **组合清单**：dsh-web-app/presets/*.patch.yml + cordis.patch.yml（565 行，枚举了 web GUI 的全部 60+ 插件）。
> 原仓：github.com/deepseek-ai/deepseek-harness（monorepo：apps/web=Vite shell，packages/client/*=UI 插件，packages/core/*=宿主内核）。
>
> 只读纪律遵守声明：对 dsh 安装目录全程只读（cat/grep/awk/node 读文件），未执行其中任何 git/npm 脚本，未写入该目录一个字节，未触碰运行中宿主进程。

---

## 一、UI 解构（会话流 / 工具卡 / 审批交互的组件与状态管理写法，文件级出处）

### 1.0 工程形态：不是"一个前端"，是"宿主 + 浏览器插件联邦"

- **宿主侧**：`dsh-host-webserver`（node:http 路由宿主：命名路由/升级路由/索引变换 + 单一 fallback 服务 SPA dist；默认 127.0.0.1 loopback-only，无 TLS 无鉴权——设计前提是"本机操作员"）；`dsh-api-gateway`（Typert RPC：unary 校验/编解码 + 多路复用流）；`dsh-api-session-controller` 等控制器插件。
- **浏览器侧**：`dsh-web-frontend/dist`（Vite 构建的薄 shell：index.html 825B + index-*.js 633KB）——shell 只负责 boot：等待 `__DSH_BOOT_READY__` → `window.__ModuleLoader__.create({boot: __DSH_BOOT__, staticModules, loadBundle: __DSH_TRANSPORT__})` → 预取 immediate 层 → 起一个 Cordis Context → 渲染进 #root（boot 进度页 → 失败页）。**所有功能 = 浏览器懒加载的插件 bundle**：每个 `dsh-client-ui-*` 包发布 `lib/client.js`，形如 `window.__ModuleLoader__.load({id, factory:(require)=>{...}})` 的工厂注册；combo 合并脚本按行共享、失败行至多 3 次请求补救、HMR 换 revision URL 热替换（`dsh-client-modules` README：启用插件→加 Loader 项，禁用→等异步效应后排空模块与样式）。
- **平台模块表**：shell 冻结 `PLATFORM_MODULES`（React、Cordis、静态 UI 库），动态 bundle 的 externals 一律查这张表——第三方插件与第一方插件同一加载律（`dsh-client-modules`）。
- **版本事实**：React（jsx-runtime 契约，具体版本打进 vendor 不可直读）、Lexical 0.49（`@lexical/*` region 路径可见）、zustand vanilla + immer（dsh-client-store 直接 import）、KaTeX（TeX 渲染）、Shiki（语法高亮）、xterm（`ui-sidebar-terminal` 的懒块 client.terminal.js）、61 个语言 JSON。
- **UI 插件清单**（cordis.patch.yml）：ui-layout / ui-theme / ui-sidebar / ui-workspace / ui-session / ui-conversation / ui-chat / ui-tool / ui-approval / ui-user-questions / ui-commands / ui-composer 件 / ui-subagent / ui-trajectory / ui-jobs / ui-goal / ui-plan / ui-skill / ui-deliverables / ui-model-selection / ui-permission-presets / ui-shortcuts / ui-message-feedback / ui-renderer / ui-primitives / ui-sidebar-right / -terminal / -files / -documentpreview / -browser / ui-settings×10 / ui-plugin-manager / ui-cordis / ui-open-in-app / ui-attachment / ui-reference / ui-brand-official …（60+）。

### 1.1 宿主↔浏览器通信层（会话流的底座）

出处：`dsh-client-connection/lib/client.js`（原 `packages/client/connection/src/client/{connection,rpc}.js`）+ `dsh-api-gateway/README.md`。

- **unary RPC**：`POST /api/<endpoint>`，信封 `​{type:"client-request", rpcId, method, payload}` → `​{type:"server-response", rpcId, result:{ok,value|error{code,message,details}}}`；rpcId 回执核对；目标白名单正则防路径穿越。**二进制回包** = multipart/form-data：metadata JSON + attachments（codec:"bytes"，按 JSON path 数组回填 Uint8Array 到占位 null）。
- **流**：`/api/remote.mux` WebSocket 多路复用，逻辑帧 open/item/end/cancel；每逻辑流独立可取消；上行 inbox 262144B 上限（溢出 `gateway/uplink-overflow` 不关物理连接）；2s ping/pong 心跳动中间设备；每逻辑流自带 Client→Host 上行（`RemoteStream<Out,In>`）。
- **重连**：`ConnectionController`（connection.js）——generation/attempt 私有于实例不入 store；指数退避 base×factor^attempt 封顶 + **半区间随机 jitter**；`navigator` 网络态变化即刻重置序列；手动 reconnect 立即换源；sink 异常不杀泵。
- **三类流语义**（api-gateway README）：`RemoteStream`（跨物理代的单消费者流，条目标注 generation）/`RemoteSnapshotStream`（开窗全量快照+增量）/`RemoteJournalStream`（**follow-before-page + 分页 + 断线补页 + 缺口修复**，域定义区间去重/拒倒序/拒重叠）；`$events` 内部端点转发宿主事件（含 `approval/request` waterfall 模式，dsh-api-remotes/lib/types/remote-events.js）。

### 1.2 会话流渲染管线（本项目最值钱的部分）

**四段流水线：journal 流 → 装配器 → 目标视图 → 渲染器**，横跨两个包：

1. **事件入口**：`SessionEventStream`（RemoteJournalStream 绑定会话地址，api-session-controller README）只发布连续的 replace/prepend/append/settle-assistant 变更；客户端先用浏览器安全的 Session 校验器验信封再发布；`loadOlder()`（Turn 对齐页，≥50 条消息跨 2 个 turn）与 `loadThrough(seq)`（turn 跳转，200 条/页循环加载）。**Assistant 流式 = cursorless 瞬态行**：开窗带 `startedAfterSeq/nextIndex/compact stream`，每个流成员成为夹在 durable 游标之间的 client-only `assistant/live-chunk` 条目；durable `assistant/message` 到达且 step/seq/index 匹配时才"落袋"，瞬态行延迟到 `step/end` 退休（挂起中的工具身份仍可用于派发）；失败/中断的 settle 立即退休瞬态行。
2. **装配器**：`dsh-client-ui-conversation/lib/client.js → packages/client/ui-conversation/src/client/conversation/assembler.js` 的 `ConversationNodeAssembler`——"Session 拥有的增量引擎"：
   - 三注册表：`ctx.uiConversation.events`（事件定义）/ `.views`（目标快照构建器）/ `.groups`（分组规则），全部**拒绝重复键、保注册序、幂等 disposer、名册变化重建既有绑定**（声明合并扩展）；
   - Context 匹配（match/start/update 接口，durable 与瞬态同一接口）+ Turn/Step `location-index` + 依赖图 `dependents` + dirty 集 + **发布等级** none/animation-frame/immediate（受控操作同帧、批量观察合帧）；
   - 窗口替换（open/重同步/缺口修复）全量重建，连续 append/prepend/settle 走增量；settle 只重算受影响 Context，"前驱索引与依赖"刷新而不动无关节点。
3. **目标投影**：`dsh-client-ui-chat/lib/client.js → packages/client/ui-chat/src/client/conversation-nodes/*`（20 个模块）：event-projection（durable 事件→Chat 行数据，`toAssistantBlocks` 分 text/reasoning/image/tool-call/other）、message/tool/retry/turn-error/turn-max-tokens/compaction/inbox/request-prompt/process-activity/fallback… + chat-snapshot-builder 组装 `ConversationSnapshot.nodes`。
4. **视图层**（ui-chat/src/client/chat/*）：`ChatView`/`MessageItem`/`AssistantMarkdown`（KaTeX+Shiki，primitives 层声明"丢 raw HTML、限制链接、解析 ANSI"——对模型输出按不可信数据处理）/`ReasoningRow`（推理折叠）/`RunningStatus`+`RunningWhaleTail`（流式鲸尾动效）/`TurnNavigator`（turn 间跳转）/`TurnUsagePanel`+`StatsPills`（token 账本）/`CompactionCommandCard`/`GenericCommandCard`/`CommandNodeView`/`message-chrome`（消息操作条）/`register-node-renderers`（节点渲染器注册——**渲染器本身也是注册表**，插件可加）。

**滚动策略**（ui-chat/src/client/chat/use-chat-scroll.js，5 hook 组合）：`useChatViewport`（scroll/scrollEnd/interact/resize 四事件连接）+ `useChatReading`（阅读采样、follow-tail↔reading 两态，用户上滚即脱离跟随）+ `useChatNavigation`（turn 跳转 busyTurn 位、contentCommitted/reconcile）+ `useProcessScroll` + `useScrollFollow`。**铁律：自己新提交的输入永远强制回尾并取消未决采样**（`ownInput` 判定含 steering/submission 三通道）。

**提交即时回显**（api-session-controller，客户端 Session 对象）：`beginSubmission` 在 submit 点击**同一帧**同步插入 `pendingSubmissions` 气泡（含有序图片预览与持久文件引用），按 running 态与投递模式派位 transcript/queued/steering；`requestId` = 宿主 echo 的 durable 用户消息 `rpcId`；权威记录到达后**原子退休**（onRetire 恰好一次，带回附件引用让 composer 释放成功卡片、保留失败草稿）；失败/放弃立即退休；回显纯客户端内存，刷新后仅由 durable 事件重建。

### 1.3 工具卡体系（ui-tool，194KB client.js）

出处：`dsh-client-ui-tool/lib/client.js → packages/client/ui-tool/src/client/tool/`。

- **`components/ToolRow.js`**：`react.memo` 折叠披露行。行内 = 图标 + 标题 + summary（运行中 `TextShimmer` 流光；error 红/stopped 灰专属色）+ 后缀（diff 卡 +N/-M 双色统计，或自定义 summarySuffix）+ 文件路径**按钮**（`onOpenFile(path,{line})` 行号直达）或外链 a（stopPropagation 防误触折叠）+ 隐藏式 state 微标（preparing/running/error/stopped 无障碍文案）。preparing 态保留图标标题不可展开。
- **展开体 = 特化卡片模型优先级链**：askQuestion → terminal（`TerminalBlock` maxLines:∞）→ diff（`DiffBlock` maxLines:9）→ read（`ReadBlock` 8）→ image（`renderSlot("tool.call.images",...)` 插槽渲染+懒加载图）→ search（含 recovery 提示行）→ web → details（`ToolDetails` 检查器）→ 通用 IO 双栏（input/output 标签+分隔线）→ 代码变体整块 CodeBlock。**每个模型是纯函数**：`models/{terminal,diff,read,search,web,image,todo-diff,inspection,control,details-card,raw-tool-call,auto-review-denial}-card-model.js` 把工具结果 JSON 投影为视图模型 + 本地化标签——**新增工具卡 = 注册一个 model + 一个 row 视图，零侵入**。
- **`ToolCallTree.js`**：嵌套子工具（工具内再调工具）树；`tool-call-arguments-partial.js`：参数 JSON 流式部分到达时的渐进渲染；`toolviews/`：GenericToolCard + read-family/read-image/file-mutation/search/web/todo/plan-summary/details-row 专用行；`components/AskQuestionCard.js`/`QuestionToolRow.js`：模型向用户提问的卡片（多选问题内嵌在工具卡内直接作答）。

### 1.4 审批交互（三层：宿主缝隙 → 事件转发 → composer 接管）

- **宿主缝隙**：`dsh-user-approval`（`src/index.ts` ApprovalService）——一次性审批、`approval/request` **waterfall 事件**（answerer 链：owned 则答、否则 next() 委托）、无终端 answerer = `unavailable` **fail-closed**；policy ask/never（never 在 waterfall 派发前强制，后注册的 listener 无法绕过）；请求必须 turn-enclosed（turn = durable 日志的提交/重放边界）；abort 即撤回问题，迟到作答丢弃；**每次请求与结果都写进会话审计日志，模型只看到工具结局不看到审批 UI**。
- **浏览器侧**：`dsh-client-ui-approval/lib/client.js`（全文 14KB，本报告全读）——inject [`sessions,remote,uiSession,slots,locale`]；注册 `approval/request` 远程 waterfall 消费者：`PendingApproval` 类（`Promise.withResolvers` + abort signal 监听 + `#delegated` Symbol 区分"委托给下一 answerer"与"出错"；answerable 单射语义，二次 settle 抛错）→ 经 `registerPendingInteraction` 挂到会话的 pending 交互位。
- **`ApprovalPanel.js` = composer takeover**（输入条整体被审批卡替换，非弹窗非系统对话框）：警告色顶条（StateDot + "等待审批"）+ 标题（displayReason 本地化优先于裸 reason）+ `renderSlot("conversation.approval.detail")` 让工具包贡献详情（`ui-chat/ApprovalCommand.js` 从相关联 tool-call 节点 JSON.parse 出 command 参数显示待批命令）+ 双按钮（拒绝=危险悬停色 / 允许一次）。
- **键盘与输入法纪律**（可直接抄级）：Enter=允许一次、Esc=拒绝；**IME 三重守卫**（isComposing / keyCode 229 / compositionEnd 后一拍拦截）；焦点不在面板内不响应；按钮/链接上的 Enter 不劫持；修饰键排除；answered 乐观置位 + aria-busy，answer 失败回滚可再答；`data-approval-key` 供外层点击判定豁免区。

### 1.5 输入器（composer）与命令体系

- **编辑器**：Lexical 富文本（`ui-conversation/src/client/input/editor/`）：`DraftEditor`/`ComposerContentEditable`/`chip-node`+`ReferenceChip`（@/路径 引用芯片是编辑器内联节点而非文本）/`DecoratorPortals`/`claim-decor`（命令 claim 装饰）/`span-map`/`text-ref`/`keymap`；`input/blocks.js` + `decorations.js` 定义块模型；图片粘贴走 attachment 服务。
- **提交状态机**：`input/machine.js` **纯函数状态机**——phase: plain → claimed（命令 token 被认领）→ adjudicating（Enter 后裁决命令归属）→ submitting；`argsAfter` 剥离 claim token 取参数；`mintAttempt` 铸造尝试（draftSnapshot 存证）；失败回滚用 `commit-draft` + `retainSuffixOf` 保留用户后缀；busy 相位拒绝二次 claim。`submission-policy.js`（空内容拒发）+`submission-analytics.js`。
- **QueueDock**（`queue/QueueDock.js`）：运行中再输入 → 入队坞（steering 派位），消息进 transcript 还是 queue 由 running 态与请求投递模式决定；inbox watermark 到达 claim seq 后 Chat/QueueDock 排除 stale 行。
- **命令体系**：`ui-commands`——"/"弹出注册表三态解析：popupSelect（`/model` `/permission` 有 UI）/action（客户端动作）/execute（宿主命令直执）；**命令行绝不静默降级为普通 prompt**；宿主命令可被装饰补 UI。技能（`ui-skill`）与 `/plan` 同管道。

### 1.6 状态管理写法（三层：引擎 → hook 桥 → 插槽）

- **引擎（React-free）**：`dsh-client-store/lib/index.js`（全文 6KB，本报告全读）= zustand/vanilla createStore + subscribeWithSelector + immer produce（update 走 draft mutator）/ set 走 devFreeze 深冻结 + **rafBatch**（flush:'raf' 时一帧合并通知；默认 sync 保受控输入同帧回显）+ **手写 localStorage 整值持久化**（不用 zustand persist 的原因写得很清楚：其 partialize 会把原始值 state 展开成 {0:'h',1:'e'...}，损坏发生在序列化之前无法用选项修复）。`defineStore({init,persist,actions})` 声明式 → StoreHandle（actions 自动绑 draft mutator；persist key 可带 scope 后缀；clearPersisted）。订阅者异常隔离（notifySubscribers 拷贝派发 + console.error 标签）。
- **hook 桥**：`dsh-client-ui-renderer/lib/client.js`——**全 UI 只有一个 useSyncExternalStore 桥**（useSyncExternalStoreWithSelector），**按源在绑定点缓存** selector hook；HostContext/RootBindingContext/ScopeBindingContext 三层 Context；`SlotOutlet`/`RootOutlet`/`FactoryOutlet` 用 useSyncExternalStore 订阅宿主**版本号**（注册变化 bump version → 出口重渲）；`FactoryOccurrence` = 工厂竞争选择（多个 provider 注册同名工厂时的选择与纪元）；`StrictSessionEntry` = 会话域条目级错误隔离（onEntryError 上报槽位与是否移除）。
- **插槽系统**：`dsh-client-ui-slots`（契约）+ renderer 的 registry/scoped-slots/bindings——**注册侧"席位"（store seat / 渲染 seat / 组合器接管 selector）与渲染侧"出口"分离**；composer takeover（审批/提问）就是"组合器接管"席位的一个 consumer（`props.matched` 由 selector 匹配 pending 交互）。
- **会话域**：`dsh-client-ui-session → session-provider.js` `renderSessionArea(binding,{empty,children})`——每个会话一个绑定域，会话切换 = 换域不换树。

### 1.7 布局、主题与周边

- **三栏 AppFrame**（`ui-layout`）：左导航（可折叠 56px rail，底部钉 Settings）+ 中会话 + 右侧栏（`ui-sidebar-right`：每会话一个停靠面、边缘锚定面板、会话头展开钮、tab 型注册表 + Tab 域携带"怎么被导航到/活多久"）；**右栏先让位、其下保留宽屏轨道；占用者可全屏**。
- **主题**（`ui-theme`）：light/dark/system + 内容字号 10–22px；持久化在宿主 `$DSH_HOME/cordis.patch.yml` 的 ui-theme 命名空间；**`--dsw-*` 双层令牌**（alias 语义层 / specific 具体层，第三方主题经 ctx.theme 注册 alias 覆盖）；同步 bootstrap 脚本先于 shell 注入防调色板闪白。
- **右侧栏三件**：`ui-sidebar-terminal`（xterm + 会话 workspace 执行 + 重命名 tab + **页面重载后恢复保留进程** + 收起侧栏命令继续跑 + 关 tab 请求终止 + tab 补全；终端权限=执行环境系统用户，独立于 Agent 权限）；`ui-sidebar-files`（workspace 树 + 直连 watch 自动刷新 + 手动重载）；`ui-sidebar-documentpreview`（MD/代码分页文本、PDF/HTML/图/表格整字节、未知扩展名纯文本、**Word/PPT 本地转 PDF（libreoffice-kit）**、渲染器注册表可扩展、文件状态/wrap/自动手动重载）。
- **工作区/会话列表**（`ui-workspace`）：分组/平铺、新建/重命名/重排/搜索/**fork(atSeq 选定前缀)**/archive/删除；行菜单与悬停按钮是**插槽列表**可被插件扩展；pending 交互黄点；空闲未归档会话有计划任务时钟标 + 悬停卡列任务；子代理来源会话隐藏。
- **其余面板**：`ui-subagent`（后代目录+用量+只读执行记录+@引用）；`ui-trajectory`（turn/step 账本+计时概览+记录检查器+**只渲染可见行**+流式跟尾）；`ui-jobs`（live 计时行/settled 折叠区/输出面板展开即订阅流、收起停流）；`ui-goal`（durable 态+进程本地激活双显示、编辑/暂停/恢复/清除、/goal 落 Command input 气泡）；`ui-plan`（/plan 进、芯片退、提交自动开右栏审查、重载自历史恢复）；`ui-deliverables`（turn 改动文件卡+宿主行数+点开该文件审查 tab+行内代码引用→正确侧栏）；`ui-model-selection`（/model 弹窗与 composer 控件同源，effort 联动，不可用模型禁用 composer）；`ui-permission-presets`（Read Only/Workspace Write/Full + EXP Auto，可见 Full/Auto 需各自风险确认）；`ui-shortcuts`（Mod+/ 命令引用、录制/清除/恢复）；`ui-message-feedback`（点赞点踩+分类备注，**log-only 不进模型上下文**）；ContextMeter（`contextPressure` 投影环形占用+breakdown 三段条：system/tools/messages，紧凑 K/M 本地化数字）。

---

## 二、功能清单 + 成熟度（1–5）

| # | 功能域 | 细目 | 成熟度 | 依据 |
|---|---|---|---|---|
| 1 | 多会话/工作区管理 | 分组列表、fork(atSeq)、archive、搜索、队列、重排 | **5** | ui-workspace + api-session-controller（投影缓存冷读不启 Agent） |
| 2 | 流式会话渲染 | token 级流 + 瞬态行 settle 原子替换 + 推理折叠 + 鲸尾动效 | **5** | ui-chat conversation-nodes + live-chunk 语义 |
| 3 | 工具卡体系 | 12+ 特化模型、嵌套子工具树、参数部分渲染、检查器 | **5** | ui-tool models/toolviews |
| 4 | 审批/人机交互 | waterfall 审批、composer 接管、ask-question 卡、计划审查 | **5** | dsh-user-approval + ui-approval + ui-user-questions |
| 5 | 断线恢复与事件一致性 | generation + 退避 + journal 补页 + 快照重建 + 信封校验 | **5** | client-connection + RemoteJournalStream 契约 |
| 6 | 输入器 | Lexical 芯片引用、命令 claim 状态机、队列坞、enter 行为设置 | **4** | ui-conversation input/*（能力顶级；复杂度对探隐过高） |
| 7 | 浏览器插件化 UI | 模块加载/combo/失败补救/HMR 热插/插槽工厂 | **5**（平台能力） | dsh-client-modules + ui-renderer |
| 8 | 终端侧栏 | xterm、进程保留恢复、tab 补全、多 shell | **4** | ui-sidebar-terminal（client.terminal.js 懒块） |
| 9 | 文件与预览 | watch 树、MD/PDF/HTML/图/表格预览、office 转 PDF | **4** | ui-sidebar-files/documentpreview + libreoffice-kit |
| 10 | 子代理可视 | 后代目录、token/时长、continuable 区分、@引用 | **4** | ui-subagent |
| 11 | Trajectory 账本 | turn/step 边界、计时条、记录检查器、可见行渲染 | **4** | ui-trajectory |
| 12 | 后台任务面板 | live 计时、输出流按需订阅、终止 | **4** | ui-jobs + api-job-controller |
| 13 | Goal/Plan/Todo | 三件套面板齐备、reload 恢复 | **4** | ui-goal/ui-plan/TodoPanel |
| 14 | 模型/权限/技能选择 | /model /permission /技能 同管道、风险确认 | **4** | ui-model-selection/permission-presets/skill |
| 15 | Token/上下文计量 | TurnUsage（cache 命中拆分）+ ContextMeter + StatsPills | **4** | ui-chat TurnUsagePanel + ui-conversation ContextMeter |
| 16 | 快捷键/无障碍/国际化 | 可录制快捷键、aria 全面、IME 守卫、61 语言包 | **4** | ui-shortcuts + 各组件 aria/IME 处理 |
| 17 | 反馈/遥测 | like/dislike（log-only）+ otel（仅桌面，Web 明确排除） | **3** | ui-message-feedback + api-session-controller 头注 |
| 18 | 主题系统 | 双层令牌、昼夜、字号、第三方主题注册 | **4** | ui-theme --dsw-* 体系 |

综合：**这是一套工程完成度和契约严谨度都顶级的 agent 宿主驾驶舱**（大量 README 把不变量、失败语义、竞态处理写成行为契约，如"订阅者异常不杀泵""settle 只退休具名 attempt"）。

---

## 三、业务使用流（作为 agent 宿主驾驶舱的真实工作流）

以操作员视角走一遍（每步标注 UI 出处）：

1. **启动**：`dsh web`（或默认 profile 组合 dsh-web-app/cordis.patch.yml）→ host-webserver 监听 127.0.0.1 → 浏览器开 shell：boot 进度页（每插件条目状态）→ 模块图装载 → Cordis Context 起来 → 三栏 AppFrame。
2. **开新会话**：左栏 New Session → 选 Workspace（无则调目录选择器插件；"添加工作区"无选择器时不可用——能力探测式降级）→ 空状态 Hero（EmptyHero）。
3. **配置**：composer 模型控件或 /model 选模型+推理力度；/permission 或 composer 选权限预设（Full 需风险确认勾选）。
4. **提交**：输入（可拖图/粘贴图/@文件芯片引用/斜杠命令）→ Enter → **同帧回显 pending 气泡**（`beginSubmission`），流式期间自己输入可作 steering 入 QueueDock。
5. **观察**：assistant 文本/推理流式（鲸尾指示）→ 工具卡 preparing→running(shimmer)→settled；点开 diff 卡看 +12/-3；点文件按钮带行号直开右侧栏预览；ContextMeter 看占用环；TurnNavigator 跳历史 turn；Trajectory tab 看计时账本。
6. **审批**：危险工具（沙箱外写/网络/越权命令）→ **输入条被审批卡接管**：显示待批命令（ApprovalCommand 从关联 tool-call 抽出）→ Enter 允许一次 / Esc 拒绝；或事先 /permission 切 Read Only。全程审计入会话日志。
7. **人机问答**：模型 ask_user_question → 工具卡内多选直接作答（AskQuestionCard），或 plan 模式提交计划自动开右栏审查面板（批准/驳回/忽略）。
8. **并行作战**：模型起 subagent → 父会话头目录出现子代理行（运行态/token/时长）→ 点开可读执行记录、continuable 的可续问可独立 Stop；后台 job 在会话头 jobs 控件看 live 计时与输出流。
9. **收尾交付**：turn 结束出 deliverables 改动文件卡（行数统计，点开逐文件审查 tab）；present 类工具产出的文件有独立交付卡；open-in-app 直开宿主文件管理器。
10. **复盘治理**：TurnUsagePanel 查 cache 命中率与 reasoning 拆分；like/dislike 写反馈；会话日志导出；goal 面板跟长任务自动续轮；Settings→Plugins 热插插件并看到页面级同步失败重试。

---

## 四、对探隐判决

### 判决：**仅参照**（UI 模式与交互律照抄；代码不复用、不二开；遥控接入另走两条薄桥）

**置信度：0.90（结构性高置信——基于契约耦合度的硬证据，非主观权衡）**

#### 4.1 为什么不能"复用/二开"当探隐的驾驶舱

1. **GUI↔宿主是硬焊契约，不是通用前端**。web GUI 的每个像素都建立在 `/api` Typert unary RPC + `/api/remote.mux` WS 多路流 + `$events` 事件转发 + SessionController/JobController/TerminalController/WorkspaceController 投影体系 + 审批 waterfall 之上；60+ client-ui 插件靠 `inject: ["sessions","remote","uiSession","slots","locale",...]` 的 Cordis 服务网活着。让 dsh GUI 驱动探隐 CLI = **探隐用 Python stdlib 重实现 dsh 宿主 API 面**（会话 journal 流语义、投影缓存、审批事件、模块/bundle 服务……），保守估计万行级且锁死 0.2.0-rc 契约版本——这正是探隐法律明文禁止的"底座插件"路线。
2. **产物形态不可二开**。前端发布物是编译 bundle（发布时显式排除 .map），可编辑源在 GitHub monorepo（MIT，合法可抄**思想**）；但 React + Lexical + zustand + 自研模块加载器 + 60 包插件联邦与探隐"零框架零构建语言律"正面冲突。
3. **连"嵌 iframe"都不成立**：GUI 无鉴权设计前提是 loopback 本机操作员，且会话状态全在其自有宿主进程内。

#### 4.2 遥控器家族的正确接线（判决的核心部分）

"dsh 作为遥控器接入探隐 CLI"字面方向（dsh GUI → 探隐）**不成立**；但反向与旁向两条薄桥今天就可建，且完全符合探隐四层架构：

- **桥 A（探隐 → dsh，dsh 入编"可平权遥控的 harness 家族"）**：dsh 原生暴露三个被驱动面——
  1. `dsh --profile headless "任务" --json --session-id <id>`：单任务 JSON 事件流 + 会话续用（dsh-headless README）；
  2. `dsh --profile acp`：标准 ACP（agentclientprotocol.com）stdio server——建/续会话、选模型力度、挂 MCP、提交/取消、语义更新（dsh-acp README）；
  3. `dsh-sdk-jsonrpc-server`：stdio JSON-RPC，每 sessionId 一会话、排队 prompt、**流回全部会话事件与 agent 状态迁移**。
  探隐遥控器已能驭 opencode，同法加一个 dsh 适配器即可。注意方向：**dsh 不是探隐的遥控器，而是探隐遥控器可驾驭的又一个战士级 harness**——这与"任意 harness 平权遥控"的架构表述完全一致。
- **桥 B（dsh 战士 → 探隐能力，MCP 薄桥）**：探隐把红队判据/工具暴露成 **MCP server（stdio JSON-RPC，Python stdlib 零依赖可实现）**，dsh-mcp-client 挂载后 dsh 的模型即可调用探隐工具（`mcp__tanyin__xx` 命名），结果以 GenericToolCard 呈现在 dsh GUI。桥厚度 = 一个子进程 + JSON-RPC 循环。这是唯一"在 dsh 界面里看得见探隐"的法律内路径。
- **桥 C（dsh GUI 当探隐驾驶舱）= 拒绝**：即 4.1 第 1 条，唯一实现方式是探隐冒充 dsh 宿主（最小契约子集也 >3k 行且随上游漂移），明确不做。

#### 4.3 翻案条件（何时可改判"二开/复用"）

1. dsh 开放**外部会话提供者契约**——把 SessionEventStream/journal 后端抽象为可插拔 transport（现状：`$events`/journal 全指向本进程 SessionManager，无缝隙）；
2. 探隐放弃零框架零构建法律（宪法级，实质不可能）；
3. dsh 前端发布可独立嵌入的 runtime + 文档化 API（现状：无）。
三者任一成立才翻案；在此之前 UI 层面只抄模式（第五节）。

---

## 五、可偷的 10 条（注明落到探隐哪页）

| # | 偷什么 | 落到探隐哪页 | 出处（文件级） |
|---|---|---|---|
| 1 | **审批 composer 接管律**：挂起审批时输入条整体替换为审批卡（非弹窗）；Enter=允许一次/Esc=拒绝；IME isComposing+keyCode229+compositionEnd 三重守卫；乐观禁用+失败回滚+aria-busy；abort 即销卡；高危悬停危险色 | **会话页**（探隐高危命令审批）+ **控制面**（权限预设切换提示） | ui-approval/src/client/ApprovalPanel.js；dsh-user-approval（fail-closed waterfall + 审计入日志） |
| 2 | **工具卡三态披露行**：单行 summary + state 微标 + 运行流光 shimmer + 特化展开体优先级链（terminal→diff→read→search→web→io）+ 文件路径按钮带行号 + diffStat +N/-M 前缀；**卡片模型=纯函数注册制**（新工具零侵入） | **会话页**（探隐每个红队工具一行一卡） | ui-tool/src/client/tool/components/ToolRow.js + models/*-card-model.js |
| 3 | **journal 流 + 瞬态行 settle 语义**：会话=seq 单调追加日志；流式块是夹在 durable 游标间的瞬态行，settle 只退休具名 attempt 的瞬态行、其余节点不动；断线走尾页缺口修复、重连 follow-before-page 开窗 | **会话页 + 控制面**（探隐 webui 会话流的刷新/重连零鬼影模型） | api-session-controller（SessionEventStream）+ ui-chat conversation-nodes/event-projection.js |
| 4 | **提交同帧回显 + requestId 关联退休**：submit 点击当帧插 pending 气泡（transcript/queued/steering 三派位）；宿主 echo requestId=rpcId；权威记录到达**原子退休**、失败立即退休并释放附件占位 | **会话页**（探隐操作员发令的即时手感） | api-session-controller（beginSubmission/onRetire 契约） |
| 5 | **滚动阅读策略状态机**：follow-tail↔reading 两态，上滚即脱离跟随；**自己新输入强制回尾并取消未决采样**（三通道判定）；turn 跳转 busy 位；resize reconcile | **会话页** | ui-chat/src/client/chat/use-chat-scroll.js（5-hook 组合） |
| 6 | **输入命令 claim 状态机 + 队列坞**：/命令 claim 装饰→adjudicating→submitting 纯状态机；draftSnapshot 存证与 retainSuffixOf 回滚；运行中输入进 QueueDock（steering）而非硬塞 transcript | **会话页**（探隐 CLI 命令面板与转向队列） | ui-conversation/src/client/input/machine.js + queue/QueueDock.js |
| 7 | **ContextMeter 环形占用 + breakdown**：contextPressure 投影驱动 14px SVG 环 + 百分比；点开三段着色条（system/tools/messages）+ K/M 紧凑本地化数字；无数据不渲染 | **会话页 + 战局总览**（红队长会话的上下文预算仪表） | ui-conversation/src/client/skeleton/ContextMeter.js |
| 8 | **TurnUsage token 账本**：每回合可点开：cache 命中%（=cacheRead/(total-output)）/uncached input/cache read/cache write/output/reasoning 拆分；StatsPills 常驻摘要 | **战局总览**（探隐按战士/回合聚合的成本视图） | ui-chat/src/client/chat/TurnUsagePanel.js + StatsPills.js + token-format.js |
| 9 | **子代理后代目录 + 只读执行记录**：父会话头列全部后代（运行态/token/活动时长）；one-shot 开=只读执行记录，continuable 可续问可独立 Stop；@引用把运行中子代理标签插入消息（不解析成地址） | **战局总览**（探隐多战士编排视图的直接蓝本） | ui-subagent（README 契约 + @ source 语义） |
| 10 | **快照存储三律（零框架可移植）**：① store=getSnapshot/subscribe/update(draft) 的 observable + **rAF 合帧通知**（受控输入 sync 同帧例外）；② 全 UI **单一 useSyncExternalStore 桥** + selector 浅比较按源缓存；③ localStorage 整值持久化要防"原始值被展开"的序列化损坏 | **控制面**（探隐 webui 全局状态层的性能律，纯 JS ~50 行可重现） | dsh-client-store/lib/index.js + ui-renderer/src/client/bind.js |

**附赠 3 条（不计入十）**：① 模块加载失败补救协议（combo 失败行至多 3 请求、注册去重不重放）——探隐 webui 静态资源分段加载可抄；② `--dsw-*` 双层设计令牌（alias 语义层可被第三方主题整体覆盖）；③ inbox watermark 排除 stale 队列行的"权威-回显"合流规则。

---

## 附：证据快照（关键包与文件索引）

- 安装根：`/opt/homebrew/lib/node_modules/@deepseek-ai/dsh/`（package.json v0.2.0-rc.2, MIT, bin: lib/bin.js=commander CLI）
- 前端 shell：`.../node_modules/@deepseek-ai/dsh-web-frontend/dist/`（index.html + assets/index-5SrrfWpU.js 633KB + vendor 740KB + langs/×61 + fonts/×65）
- UI 插件包群：`.../node_modules/@deepseek-ai/dsh-client-ui-*/lib/client.js`（全部未压缩、带 #region 原仓路径注释；重点已全文/分段读取：ui-approval 14KB 全文、client-store 6KB 全文、ui-tool ToolRow、ui-conversation assembler/machine/ContextMeter、ui-chat event-projection/ApprovalCommand/use-chat-scroll/TurnUsagePanel、client-connection connection/rpc、ui-renderer 扫描）
- 组合清单：`.../dsh-web-app/cordis.patch.yml`（565 行）+ presets/{standard,ptc,minimal,cordis}.patch.yml
- 宿主通信：`dsh-host-webserver`（node:http 路由宿）/`dsh-api-gateway`（Typert RPC+mux WS）/`dsh-api-remotes`（$events 含 approval/request waterfall）/`dsh-api-session-controller`（journal/快照流契约，README 极详尽）
- 被驱动面：`dsh-headless`（--json --session-id）/`dsh-acp`+`dsh-acp-app`（ACP stdio server profile）/`dsh-sdk-jsonrpc-server`（stdio JSON-RPC 会话流）；`dsh-mcp-client`（挂外部 MCP server = 桥 B 的对接面）
