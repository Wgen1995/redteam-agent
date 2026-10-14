# ARTEX 深读 · 视角4 工程可靠性（子代理 ab90c31d，2026-10-11）

> 只读实勘：llmpool/selfupdate/traffic/llmrec/SSE/notify。舰队共 5 路，此为第 4 路。

## ① 机制详解

**llmpool（llmpool/pool.go、health.go、server/llmpool.go）**——Provider 装饰器实现的多配置故障转移链。链序=全局激活配置（Rank=MaxInt-1）→其余按 priority DESC、pool_exclude 排除；绑定/pin 的配置默认独占失败即失败，可选 llm_pool_bind_fallback 兜底（server/llmpool.go:147）。取号 order()（pool.go:168）跳过熔断冷却中的成员和窗口装不下的成员（estimateTokens 粗估 ~3.5 字符/token），全被过滤则强行试探链头"宁可再失败也不停摆"；同 Rank 组内原子计数器轮转分摊负载。
失败判定 shouldFailover（pool.go:231）：ctx 取消/400 不转移（400 到哪都失败），401/402/403/404/408/429/5xx/无状态码（传输层）转移。
**铁律（pool.go:82）**：只有未 yield 任何事件前才允许换下一个——流中途失败原样上抛，防重复输出污染会话。
熔断 Registry（health.go）进程级共享、重建池不清空：硬失败（401/402/403/404，isHardFailure）一次即熔断；瞬时失败连续 3 次（softTripAfter）熔断；冷却阶梯 1min/5min/30min（backoff 数组），Trips 持续累加永不衰减，恢复靠冷却到期后真实请求当半开探针，成功 Pass 全清。冷却状态异步落 PG、重启 Restore 只恢复未过期窗口（server/llmpool.go:22-55）；SetPolicy 运行时可调旋钮；UI 状态 ok/degraded/tripped+剩余冷却秒数+Reset。

**selfupdate（selfupdate/ 四文件）**——三次启动编排：①旧版下载 zip→SHA256SUMS 校验→解压→冒烟（新二进制 -h 跑 30s）→暂存 artex.new+独立 sha256→exit 75；②脚本拉起旧版→Bootstrap 复核校验和+再冒烟→rename 换装（current→old→new，失败原位放回）→exit 75；③新版启动计 attempts，HTTP 监听后活过 SettleDelay=30s 才 Settle 清标记；连续 3 次起不来自动回滚 .old（新版留 .failed），回滚也失败则删标记避免无限重启（bootstrap.go:110-131）。
安全五道闸（github.go）：更新源写死不可配（防 RCE）、https+域名白名单、CheckRedirect 每跳复查、独立 Transport 不受全局 InsecureSkipVerify 影响、SHA256SUMS；512MiB 解压上限、下载前写权限探针、临时件同目录保 rename 原子、dev 构建禁用更新。

**traffic（traffic/traffic.go）**——内嵌 go-mitmproxy，addon 完整明文交换写 SQLite 索引：≤256KiB 正文内联、大正文溢出 sha256 内容寻址 blob（8KiB 预览+magic 标签），FTS5 trigram contentless 任意子串+中文全文检索（无 FTS5 优雅降级）。MITM 失败开门（fail-open）：代理自身错误把 host 加入透传集合，请求照常到达但不记录（traffic.go:399-431）。全局出网代理 atomic.Pointer 热切换；默认强制直连防环境变量 502。删除走 rename 进 _delete_staging（可逆）+事务+后台 unlink；空间回收 32MiB 分块持锁、块间放写锁（record 在代理应答前运行不能被卡）。

**llmrec（llmrec/llmrec.go、capture.go）**——Provider 录制装饰器：轻量 usage 计量永远开启（失败/中断调用也计），重报文由 llm_record 开关；ctx 挂 Capture 让传输层回填原始线上报文，含被 SDK 丢弃的重试尝试（诊断限流/网关的关键证据）；session 串解析任务/工人归属。

**SSE（server/broadcast.go、server/server.go:2926-3075、logsink.go）**——per-task 发布订阅，256 缓冲满即丢（活币优先，DB 是真相）；streamActivity 先订阅再重放（无窗口间隙），Last-Event-ID 优先于 ?since，id: 行让浏览器自动重连带游标，500 条/批补 backlog，20s ping，X-Accel-Buffering:no。logsink tee 进 3000 条环形缓冲+异步落库，重启恢复最近 100 条。

**notify（notify/notify.go）**——纯标准库叶子包，Channel 强制无状态（凭据每次从 cfg 传入）；严重度门槛"未知=0 分"，任何 min_severity 都把未知级别挡在外——存疑不推，防误报刷屏。

## ② 妙处
1. "首个事件前才可转移"安全窗口铁律（pool.go:75-81）：流式 failover 正确性化归为时序判断；401/402/429 全发生在建连期天然落在窗口内。
2. 熔断状态进程级共享+落库重启恢复：一个任务发现欠费全进程立刻跳过，重启不重复撞墙。
3. selfupdate 全部易错逻辑放 Go 而非 sh/bat 双份脚本；换装前双冒烟+attempts+回滚失败兜底，三连败每条路径有归宿。
4. traffic 回收"分块持锁、块间让锁"精确保护 record() 关键路径；staging rename 让删除在事务提交前完全可逆。
5. Broadcaster 丢弃换活币+DB 游标补洞：宁可客户端重连补数据，绝不让推送反压拖慢引擎。

## ③ 弱点/隐患
1. pool.go:213 正则从错误文本抠 HTTP 状态码（SDK 无类型化错误）——SDK 改文案即静默失效。
2. 熔断无抖动：冷却到期瞬间所有并发任务同时重试同一配置；429 与 5xx 共用冷却阶梯欠 granularity。
3. Complete 非转移错误也调 Pass（pool.go:142）——确定性 400 会清掉正在累积的失败计数。
4. traffic 透传集合只进不出、无 TTL：一次瞬态 h2 故障让该 host 永久停录直到重启；proxyCausedErr 也是字符串匹配。
5. 交换 id=秒级时间戳+seq%10000，超 1 万 req/s 理论互相覆盖。
6. SHA256SUMS 与二进制同信道下发，只保证传输完整性不保证发布者身份——无签名验证；llmpool 落库异步 best-effort，PG 抖动时冷却窗口退化为单进程内存。
7. logsink levelOf 靠关键词猜级别。

## ④ 探隐可借鉴（v0.8a 直接蓝图）
1. 【llmpool 整体照抄 v0.8a】链序+进程级熔断+冷却落账+三态(正常/退化/熔断)+"立即恢复"。实现用类型化错误判定（避开它的正则抠状态码之痛）；冷却状态写 TSV 账本或独立表，重启恢复未过期窗口。风险：状态按 profile id 键控，配置重建需迁移。
2. 【安全窗口铁律】所有流式 LLM 调用：首 token 前可换备胎，之后失败上抛走恢复逻辑。零成本防重复输出污染上下文。
3. 【错误分类表】400/ctx取消 不转移；401/402/403/404 硬熔断；408/429/5xx/网络 软计数 3 次；冷却 1/5/30min 阶梯+运行时旋钮。改进：429 短冷却、5xx 长冷却分开，冷却加 ±20% 抖动。
4. 【selfupdate 三段式】下载校验暂存→复核+冒烟+换装→计数 3 败回滚+Settle 30s。改进：SHA256SUMS 换成真签名（探隐已有 ECDSA 供应链 v0.7c——正好补它的无签名短板）。
5. 【SSE 断线恢复】先订阅后重放+Last-Event-ID+id: 行+批量补洞+满即丢。哈希链天然是单调游标，账本即真相源。
6. 【llmrec 双层录制】轻量计量永远开（失败调用也入账），重报文按需开；原始线上报文含被丢弃的重试——排障唯一 ground truth。
7. 【traffic 分块回收+staging 删除】TSV 账本压缩/归档同律：分块持锁、块间让锁；删除先暂存可逆再提交。复杂度高，先日志型账本再考虑。
8. 【notify 无状态渠道+未知严重度不推】通知层照此设计；"存疑不推"与精度门哲学同构。
