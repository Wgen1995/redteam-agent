# sqlmap 引擎 MANIFEST（契约 08 十二字段）

kind: cli

| 字段 | 值 |
|---|---|
| name | sqlmap |
| kind | cli（OS 进程执行；失败=非零退出/超时/部分产物；适配器输出操作日志供审计回放） |
| version | 0.1.0（W3-P1-1① 受控档） |
| 适用场景 | SQL 注入检测与受控枚举（deep-dive/nday-verify：只读检测档确认注入点→C3 疑似发现供总控复核） |
| 参数 | adapter.py --intent-id=I --out-dir=D (--plan --target=URL [旋钮] | --log-file=F | --run --goal-dir=G --target=URL [旋钮])；旋钮=--param/--level/--risk/--delay/--database/--table/--dbs/--tables/--approval/--sqlmap/--timestamp |
| 产物路径 | submissions/<intent-id>/{submission.json, operations.log[, sqlmap-output.log]} |
| 超时 | 1800s 适配器壳；guard exec 内层 --timeout=600（上限同） |
| 重试策略 | 不重试（墙拒/审批拒/sqlmap 缺失/guard 非零=blocked 提交，绝不自动安装） |
| 幂等键 | intent_id（intent done 且 submission.json 存在→重入跳过） |
| 纪律能力声明 | max_op_level: 读／视角上限: L1（检测+受控枚举；数据外带面旗标结构性禁令） |
| 工具依赖 | sqlmap（运行时绝不自动安装——契约 10 §4；--sqlmap 显式路径或 PATH） |
| 验签公钥 | 不适用（系统包管理分发；tools.lock 键待批次 6 类全量化时补） |

## 参数墙五件（W3 受控档——argv 只由白名单旋钮拼装，无透传通道）

1. **--delay 强制**：缺省注入 1s；墙区间 [0.5, 60]（下限=防锤击，上限=异常值拒收）。
2. **禁碰端口**：目标 URL 端口 ∈ {8900, 3000, 8787, 8443} = 墙拒（交战纪律 FORBIDDEN_PORTS
   单源同值，vulnclaw 适配器同款口径）。
3. **受控顶**：--level ≤ 3 / --risk ≤ 2（guard deny-list 已拦 --level=5/--risk=3，引擎侧更紧；
   越顶=墙拒，审批不可救）。
4. **限库限表**：-D 须在 --dbs 白名单（缺省零白名单=零库可碰，fail-closed）；-T 须伴 -D
   且在 --tables 白名单。
5. **只读检测档**：--dump/--os-shell/--sql-query/--read-file 等数据面旗标不在旋钮表内
   （结构性不可达），终检再扫 FORBIDDEN_ARGS 纵深防御。

## L3 审批挂接（P1-1「--level/--risk 由 permitted_actions+L3 审批门控」）

- 触发面：--level>1 / --risk>1 / 任何 -D/-T 枚举请求。
- 核验：--approval=APR-… → goal 目录 approvals.tsv 只读（同 id 取最新行），
  decision=approved 且 command_hash == sha256(" ".join(argv))——**逐条审批锚**，
  批的就是这条命令不是意图泛授权；hash 以 canonical 形（argv[0]="sqlmap"）计算，
  安装路径不入锚（路径漂移不改变所批语义）。
- 缺省拒：缺 --approval / 行缺 / decision≠approved / hash 不符 / 文件不可读 →
  status=blocked 提交（exit 0，log 落缘由）。

## 三运行面

- **--plan**：墙预检——打印 {wall, reason, argv, canonical, command_hash, needs_approval}，
  零执行零提交产物（不伪造 done 幂等位）。
- **--log-file**：离线归一化 canned sqlmap 控制台输出（测试/复盘面）。
- **--run**：墙序=计划→审批→环境→执行；经 tanyin-guard exec（--timestamp 取
  --timestamp 或 timeline 末行只读回取——禁 datetime.now 进产物）。

## 归一化表 v1

| sqlmap 控制台 | 统一提交映射 |
|---|---|
| 运行期行 "GET parameter 'id' is '<tech>' injectable" | findings[]（C3/suspected/高；dedup=place:param+sqlmap；expected_matcher word=[injectable]） |
| 收尾汇总块 Parameter:/Type:/Title:/Payload: | 同参数并技法、Payload 随 reproducible_steps（Burp 可直贴） |
| "the back-end DBMS is X" | facts[]（kind=info，置信 0.9） |
| "all tested parameters do not appear to be injectable" | facts[]（kind=info 负面结果，置信 0.8——如实入账不静默）+ status=no-findings |
