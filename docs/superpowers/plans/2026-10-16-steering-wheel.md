# 方向盘批计划（v0.9.8 · 从展厅到驾驶舱）
依据: D4 产品形态(操作员口令+全程浏览器) + E2-S1(信任根/HMAC 通道已建) + live-recon CSAI 实测蓝图(三级刹车/队列五钮/审批三层) + 方向修正案票序。
## 铁前提
观察面投影律不破: 网页仍是只读;**写操作走窄门**——POST 路由→guard 执法→单一写入路径入账→全程留痕。零依赖律照旧。
## 第一段 · 门禁（操作员身份）
- server 增登录: GET/POST /login(口令=操作员 env TANYIN_OPERATOR_KEY 缺省随机生成并打印启动日志;会话 cookie HttpOnly+时长;错5次锁60s);全站页照旧可看,**写路由必须带会话**。
- CSRF: 同源+自定义头检查;写路由一律 POST+JSON。
## 第二段 · 五按钮（每钮=一个受管写路由）
1. 新建战斗 /api/battle/new: 参数(目标/范围白名单/预算硬顶/说明)→生成战书落 goals/scope→回 battle id;**范围白名单为必填,空=拒**——对标 ARTEX scope 自扩五系统之痛。
2. 启动/暂停/急停 /api/battle/control: 三级刹车(CSAI 实测)——暂停=注入暂停指令+说明回注;急停=终止战士进程+账本记 EXIT。
3. 介入 /api/battle/say: 对话框→DIRECTIVE 事件入 timeline(与现有介入机制同源)。
4. 审批卡 /api/approval: 待审列表(读 approvals 账)+批准/拒绝(**走 SEC-1 的 _approval_sig HMAC**,网页只签名转发,密钥在操作员会话侧)。
5. 报告下载 /api/report/download: 按现有 report_render 产物打包(先查缓存,缺则触发生成,只读聚合)。
## 第三段 · 界面
顶栏增「开战」钮(→新建表单页);对话页增输入框+暂停/急停钮;总览增审批卡区(有待审时红点);发现页增下载钮。
## TDD 与白名单
tests/test_v098_steering.py(路由+权限+guard 包装全链);白名单: cli/webui/server.py、cli/webui/static/{index,session,evidence}.html、新 login/表单页、tests/**相关**、SKILL 双胎命令面若增。禁碰: cli/ledger/**(guard 复用不改)、graph.html(画布舰作业区)。
## 验收
未登录写路由 401;范围空拒;审批无签名拒;全量零破坏;8900 实测全流程(登录→新建→启动→介入→暂停→急停→下载)。
