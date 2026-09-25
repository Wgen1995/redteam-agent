# tanyin-ledger · 账本命令箱（批次 1）

探隐 TanYin 的 13 表 TSV 账本唯一写入口。契约基线 contracts-v2（44 命令 / 147 字段 / 九门 / 10 边）。

## 用法

```
cli/tanyin-ledger <command> --goal-dir <session-dir> [--key=value ...]
```

- 退出码：0 成功 / 1 门禁失败（REJECT，账本零变更）/ 2 用法或环境错误（对齐 Strix）
- 时间戳必填 --timestamp=ISO8601（写命令确定性来源）
- 一切写命令：写前全量校验，追加目标表行 + timeline 链式哈希事件

## Windows 用法（等价入口）

入口均为带 shebang 的 python 脚本（无扩展名），Windows 下用 `py -3` 等价调用：

```
py -3 cli\tanyin-ledger validate --goal-dir sessions\G-g1
py -3 cli\tanyin-guard exec --goal-dir sessions\G-g1 -- python -c pass
py -3 cli\tanyin-canary probe --goal-dir sessions\G-g1 --tier 1
py -3 hooks\simulate.py --goal-dir sessions\G-g1 --host dsh -- curl http://x/
```

- 同目录提供 `tanyin-ledger.cmd` 等六个包装（内容即 `py -3` 调用），可直接 `cli\tanyin-ledger.cmd validate ...`；无 py launcher 时用 `python cli\tanyin-ledger ...`
- 字节纪律：仓库根 `.gitattributes` 把 *.tsv/*.state/*.norm/*.md/*.py/*.txt 钉死 LF，代码内一切写盘显式 `encoding="utf-8", newline="\n"`——账本/金样跨平台字节一致（链式哈希与双指纹依赖此红线）
- 控制台：入口启动即把 stdout/stderr 重配为 UTF-8+replace（中文 Windows GBK 控制台不再炸输出；乱码只影响显示，不影响退出码/管道语义）
- 平台门控：guard exec 界外判定只扫参数（argv[0] 是程序路径，Windows 带空格路径会被误判为主机）；canary tier1 探测载体用 `py -c pass`（原 /usr/bin/true 仅 POSIX）
- CI：`.github/workflows/ci.yml` 双平台矩阵（windows-latest + ubuntu-latest × Python 3.11/3.12）跑 `python -m unittest discover -s tests`（job 级 `PYTHONUTF8=1`，等价于 Windows 本地 `set PYTHONUTF8=1` 后再跑测试）

## 命令面（44）

| 类 | 条数 | 命令 |
|---|---|---|
| 内建 | 3 | validate / verify-chain / next-id |
| 写 | 19 | add-goal add-scope add-intent add-fact add-finding add-asset add-cred add-edge add-evidence set-intent-status set-cred-status supersede-finding amend-scope matrix-set matrix-freeze append-timeline approve budget-log checkpoint |
| 查询 | 14 | unconsumed-facts pending-intents matrix-gaps converge-check next-id intent-status matrix-get scope-check budget-check cleanup-checklist redact-scan graph-neighbors graph-paths graph-horizon（图谱驱动增补 71d3b7c：只读图运算——邻接/路径/可达地平线） |
| 校验 | 10 | validate verify-chain hash-recheck matrix-audit state-rebuild set-replay-state ledger-scope-coverage ledger-tree-check ledger-replay-summary ledger-terminal-gate |
| 特殊 | 1 | matrix-init（P1 门：词表 WSTG v4.2 钉死列、基线冻结） |

## 测试与回归

```
python3 -m unittest discover -s tests       # 181 单测（含 02a §32 跳门检测 7 例 + Tier2 模拟器 8 例）
python3 tests/run_golden.py                 # 黄金回归 44 命令（21 读+20 写+3 图查询），两次执行确定性自证
python3 tests/make_fixtures.py              # 重铸夹具（13 表确定性样本）
```

## 目录

- cli/ledger/core.py：转义/147 字段 schema/ID 铸造/链式哈希（禁改：契约生成）
- cli/ledger/schemas.json：由 contracts/01 机械生成（禁手改）
- shared/VOCAB.md：词表（WSTG v4.2，版本化）
- tests/golden/：基线锁（漂移即 FAIL）

## 批次 2：门禁层（四层执法档位）

| 组件 | 层 | 职责 |
|---|---|---|
| tanyin-guard | Tier 1 | exec 流水：deny-list→scope 解析→request-ticket→参数化执行→输出兜底重 tokenize；inject=四关卡①执行点回注（vault cred-N.enc+manifest） |
| hooks/ | Tier 2 | 三宿主 fail-closed 模板+模拟器（deny-list+scope 界外拦截；阻断=非零+timeline hook-block；与 guard 共用 ledger/enforce.py 单源） |
| tanyin-egress | Tier 3 | compile：scope.tsv→egress.acl 四成分（ACL/DNS pin/OOB/infra）；verify=漂移检测；dry-run=代理模板（实代理批次 6） |
| tanyin-canary | 全档 | deploy 界外诱饵（seed 确定性）+probe tier 0-3 零容忍；结果 JSON 落 timeline |
| tanyin-budgetctl | Tier 0 | enforce 预算树余量+rate 速率熔断（超限 REJECT 落账） |
| special.py 扩模式 | Tier 0 | redact +16 泄漏形态（赋值/连接串/cookie/NTLM/gh 变体…）注入拦截率 100% |

出口验证：canary 各档位零容忍（tier0 scope-check 5/5、tier1 guard 5/5、tier2 hook 模拟器 5/5、tier3 真编译 ACL 5/5）；redact 注入 36/36=100%、误报 0；预算/速率限额拒绝可测（budget-exhausted/rate-limit REJECT 落 timeline）。

边界：python3 3.9+ 标准库零三方依赖；state.md 完整结构留批次 3；实代理与真宿主挂载=批次 6 靶场；vault 现为 sha256 密钥流 XOR（条目格式不变，批次 6 换真加密）。

## 批次 3：总控 SKILL 路由器 + phases.yaml 引擎 + 受管重启/恢复体系

认知与确定性分离：仓库根 SKILL.md=常驻权威集路由器（<2K token，八节结构）；phases/P0..P6.md=九门方法论按需加载；phases/phases.yaml=九门状态机声明层——执法权威仍在 44 条账本命令，断言→命令调用判定协议冻于 phases/PROTOCOL.md（批次 3 两份批次间接口合订本：协议+常驻集清单，另附干跑口径/分母就绪门）。

### tanyin-phases 子命令速查（第 11 工具；契约 09 勘误 10→11）

| 子命令 | 形态 | 语义 |
|---|---|---|
| validate | `tanyin-phases validate [--phases=P]` | phases.yaml 契约 04 合法性（gates=9 asserts=21 constants=8 back_edges=3）；金样 phases-validate.norm 入黄金回归 |
| gate | `tanyin-phases gate --goal-dir D --phase <门> [--timestamp=T]` | exit 断言执行（PROTOCOL §1 判定表）；already-passed 幂等；前置门缺=REJECT 零落账 |
| denominator-ready | `tanyin-phases denominator-ready --goal-dir D` | 分母就绪门（T3 追加件，PROTOCOL §4；只读账本，0=就绪/1=FAIL 清单/2=用法） |
| trigger-audit | `tanyin-phases trigger-audit --goal-dir D` | 触发器闭包审计（批4 T13 交付/T14 收口回注契约 09 枚举 7→8，PROTOCOL §6；只读零落账三检查=目录版本一致/触发器闭包/清单，单源目录=phases/TRIGGERS.md triggers-v2） |
| restart | `tanyin-phases restart --goal-dir D --spawn auto\|manual --timestamp=T [--session=S] [--rate-minutes=N] [--token-cost=C]` | 受管重启护栏（①verify-chain ②速率上限 ③单活跃会话 ④计入预算）+managed-restart 事件+resume-kit 重生成 |
| resume-kit | `tanyin-phases resume-kit --goal-dir D [--timestamp=T]` | 恢复注入白名单生成器（先对账再干活；缺省时间戳=timeline 末行——确定性） |
| cached | `tanyin-phases cached --goal-dir D [--intent-id=INT-…]` | 工件即缓存幂等续跑判定（intent done 且 submission.json 在位→SKIP；只读零副作用） |
| rebuild-state | `tanyin-phases rebuild-state --goal-dir D --timestamp=T [--note=文本]` | state.md 对账重建（timeline 第一事实源；链断拒绝自愈=halt 人工处置） |

- 时间戳确定性：--timestamp=ISO8601 必填处一律显式传入，禁 datetime.now() 进账本/产物（evals 与金样可重放）；Windows 等价入口 `py -3 cli\tanyin-phases validate`（同目录 tanyin-phases.cmd 包装）。
- 退出码：0=通过 / 1=门禁失败（halt，可重跑） / 2=用法或环境（对齐 Strix）。

### state.md v2 十键速览（契约 02a 勘误补记·G-6/G-10 已回注）

固定键序（全文 ≤200 行硬顶；`--- handoff ---` 分隔自由文本段；tmp+os.replace 原子写——kill -9 半写兜底）：revision（≡本次落账后 timeline 行数）→ goal → phase（九门或空）→ round → session → session_status（active/released）→ spawn（fresh/auto/manual）→ updated → resume_kit → snapshot（intents_pending/facts_unconsumed/matrix_gaps/budget_token_left 账本重算投影）。sanctioned 写者=checkpoint（升级后）与 rebuild-state；state-rebuild 对账（revision≡timeline 行数+snapshot 重算一致）。

### 干跑一屏示例（批次 3 出口①：P0-P2 零对外请求）

```
python3 cli/tanyin-ledger add-goal --goal-dir <D> … --timestamp=T    # P0 立项（八问落账）
python3 cli/tanyin-ledger budget-check --goal-dir <D>                 # 预算门在位（立项即读）
python3 cli/tanyin-ledger add-scope --goal-dir <D> --kind=include|exclude|oob …
python3 cli/tanyin-egress compile --goal-dir <D>                      # 干跑：只 compile（本地产物）
python3 cli/tanyin-phases gate --goal-dir <D> --phase P0 --timestamp=T
python3 cli/tanyin-ledger add-asset --goal-dir <D> --type=root-domain …
python3 cli/tanyin-phases gate --goal-dir <D> --phase P1 --timestamp=T
python3 cli/tanyin-ledger matrix-init --goal-dir <D> --timestamp=T
python3 cli/tanyin-phases gate --goal-dir <D> --phase P2 --timestamp=T    # matrix-freeze 由断言①真跑
# 判定：timeline 零 request:/request-ticket 事件 + verify-chain PASS（tests/test_dryrun_p0p2.py 5 例）
```

批次 3 出口验证：干跑 eval+kill -9 保真度 eval（test_kill9_fidelity——恢复后 13 表字节指纹不变+state-rebuild PASS+resume-kit 重生成）+常驻集实测 1321 token<2000+全套单测绿+42 金样面 PASS；探知项台账见 docs/design/2026-09-24-b3-discovery-notes.md（G-1..G-15 终态）。

## 批次 4：引擎层（web-blackbox 四段 / vuln-agent 适配器 / nuclei adopt / session-viz / 身份矩阵差分 / POC 重放门 / 侦察完备性）

引擎三型接线（派发前核 engines/<引擎>/MANIFEST.md 纪律能力——超 max_op_level/视角上限的 intent 拒派）：

- web-blackbox（skill 型四段 recon/surface/test/differential——A1-A8×通道×落账引擎位表+身份矩阵差分五步+护栏 AUTHZ_DIFF_PAIR_CAP=24；方法论入口=engines/web-blackbox/SKILL.md）
- vuln-agent（cli 型适配器：.vuln_agent_output→submission.json 归一化+POC 四要素门——FD 报告卡规格 b0006f2，缺四要素降级 fact 不成 finding；方法论入口=MANIFEST 归一化表，G-18）
- nuclei（cli 型 adopt：tools.lock 钉 commit+ECDSA 验签先于归一化，不过/nuclei 缺失=blocked 提交绝不自动安装；模板离线快照+templates.lock 逐文件 sha256）

其余交付：

- tanyin-replay（+.cmd）：POC 独立重放驱动三态判定（reproduced/not-reproduced/env-diff/manual→VERIFIED/REJECTED/REPAIRED 候选）；铁律 7 对外请求例外#1（scope 门链+timeline request: 记账）
- tanyin-viz（+.cmd）：session-viz 只读投影单文件 HTML（零依赖 SVG，R4；findings 实时流第六区——高危置顶▲，fb72cd5）
- tools.lock 起步版（openssl/nuclei/nuclei-templates 三键，契约 10 五字段；测试钥 TEST-ONLY，生产钥=批次 6 安装器出口，G-22）
- 侦察金丝雀：tanyin-canary recon-deploy/recon-recall（界内诱饵登记/召回率）+denominator-ready 第④断言（G-13；canary 家族全子命令零网络）
- 触发器闭包：tanyin-phases trigger-audit（八子命令面收口；目录=phases/TRIGGERS.md 版本化封闭表 triggers-v2——高危 finding 即时横向，SKILL P0 落 triggers-catalog 事件）
- 优先级调度（fb72cd5）：P3 派发=pending 按 priority=severity_expect×asset_value×exploitability 降序 Top-K（公式冻结=phases/P3.md；intents.priority 契约 01 勘误登记，物理列已落批5 T3——15→17 双列 priority/cred）

用法四行：

```
python3 cli/tanyin-replay replay --goal-dir <D> --id=EV-… [--scheme=http|https] [--port=N] [--timeout=10] [--timestamp=T]
python3 cli/tanyin-viz render --goal-dir <D> --out <path.html> [--data-only]
python3 cli/tanyin-canary recon-deploy --goal-dir <D> --value <诱饵资产值> --type <assets.type 十一值> [--note=计划编号] --timestamp=T
python3 cli/tanyin-phases trigger-audit --goal-dir <D>
```

测试与回归：

```
python3 -m unittest discover -s tests       # 全套单测（批 4 收口=395+T14 新增）
python3 tests/run_golden.py                 # 51 金样面（含 replay-envdiff/engine-*/graph*/viz-data 批 4 新面+diff-hash-recheck 评审收尾面）
```

批次 4 出口验证：引擎级夹具+差分样例对（tests/fixtures/diff-authz 全经命令铸造、重铸逐字节确定）+重放门 eval（127.0.0.1 mock 三态全链路→set-replay-state→replay-summary→verify-chain）+身份矩阵检出率（tests/eval_authz_recall.py recall=5/5）+G-2/G-12/G-13 裁决落地；探知项台账见 docs/design/2026-09-24-b4-discovery-notes.md（G-16..G-26 终态）。

## 批次 5：知识飞轮+语料入库（tanyin-knowledge 第 12 工具 / staging 流水线 / 四门槛 / 三元组 / graph.ndjson / CVE 快照）

契约 14（contracts/14-knowledge-schema.md）冻结知识库页 schema 与状态机；仓库 knowledge/=种子库（format_version=kn-v1，批次 6 安装器拷贝至 $TANYIN_HOME/knowledge/），**种子库只读纪律（R7）：写子命令（source-register/approve/commit/promote/demote/client-map add）指向仓库 knowledge/ 即 REJECT exit 1**；一切子命令 --knowledge-dir 参数化，测试与金样在临时副本上跑。批次 5 评审 I-1 起 lint 对种子库=零写入（审计行只落运行时库，出口判定命令可就地执行）。

### tanyin-knowledge 13 子命令速查

| 子命令 | 形态 | 语义 |
|---|---|---|
| init | `init --knowledge-dir D` | 骨架初始化（幂等：已初始化=PASS no-op） |
| source-register | `source-register --knowledge-dir D --path <原始素材> --origin <六枚举> --license <许可> --note <注> --timestamp=T` | 语源登记（sha256 对原始字节；KP-NNNN 递增扫 SOURCES.tsv 行键） |
| lint | `lint --knowledge-dir D --timestamp=T \| --today=日期 [--freshness-days=180]` | 机器检查四件（契约 14 schema/脱敏哨兵/dedup 查重 R10/词表版本 R14）+K1 基线覆盖率+K3 快照校验（G-32）+保鲜告警（T13；--timestamp 可由 --today 派生）；staging 过页 staged→lint-passed；kdir=仓库种子库根时零写入（评审 I-1——log/staging 审计只落运行时库，校验输出零变） |
| approve | `approve --knowledge-dir D --page STG-NNNN --approver <名> --timestamp=T [--reject --reason=…]` | 人审门（lint-passed→approved/rejected；staging.tsv+log.md 双落） |
| commit | `commit --knowledge-dir D --page STG-NNNN --timestamp=T` | approved→formal（类前缀重号迁目录+dedup 终检 R10+index/overview 重生成） |
| export | `export --knowledge-dir D` | graph.ndjson 全量重建（created 取 last_verified——双跑字节一致） |
| match | `match --knowledge-dir D --client=CLIENT-NN --asset=<指纹> --today=日期` | 先例三元组匹配（client 全等∧scope_asset 子串∧window 覆盖；[expired]/[stale] 标注；--client/--today 必填，缺=用法错误 exit 2——M-3 前 --client 缺省静默 matched=0） |
| neighbors | `neighbors --knowledge-dir D --entity=<指纹>` | graph.ndjson 实体邻接清单（A8 外推消费入口；缺导出 exit 2） |
| nday-match | `nday-match --knowledge-dir D --cpe=cpe:<vendor>:<product> --version=<v>` | K3 快照离线 CPE 匹配（零联网 R11；#snapshot-date 审计行 G-32；零命中 exit 0） |
| score | `score --knowledge-dir D --goal-dir <交战区> --vuln-class=<wstg 键> --asset=<资产> --today=日期` | K1 基线只读算分（priority=severity_expect×asset_value×exploitability 单行 JSON；Top-K 选择仍归总控） |
| promote | `promote --knowledge-dir D --page PT-NNNN --timestamp=T` | learned→core 四门槛机检（复现≥2/跨目标≥2/审批在场/无指纹泄漏——缺口清单 REJECT） |
| demote | `demote --knowledge-dir D --page PT-NNNN --refuting=<≥2 项> --note=<防护拦截\|代码修复…> --timestamp=T` | 降级 patterns/demoted（status=demoted 留档） |
| client-map | `client-map next\|add\|list --knowledge-dir D [--real-ref=<真值> --note=…] --timestamp=T` | CLIENT-NN 运行时映射（真值文件 client-map.tsv 已 gitignore，R12；add 指向种子库=REJECT） |

### 用法四行

```
python3 cli/tanyin-knowledge lint --knowledge-dir <运行时库> --today 2026-09-24     # 入库前机检（四判据之一）
python3 cli/tanyin-knowledge match --knowledge-dir knowledge --client=CLIENT-01 --asset=shop.example --today 2026-09-24   # P2 开局先例检索（只读）
python3 cli/tanyin-knowledge nday-match --knowledge-dir knowledge --cpe=cpe:apache:log4j --version=2.14.1   # P3 asset-added 回边（G-18）
python3 tests/eval_knowledge_spotcheck.py --knowledge-dir knowledge --origin cnpen --today 2026-09-24       # 双库抽查（§9.4，探针在临时副本跑）
```

测试与回归：`python3 -m unittest discover -s tests`（全套）+ `python3 tests/run_golden.py`（54 金样面含 kn-export/kn-match/kn-nday 三面）+ `python3 -m unittest tests.test_eval_scripts`（出口 eval 自检）+ `python3 tests/eval_reverse_verify.py --goal-dir tests/fixtures/G-g1`（反向验证双向断言）。

批次 5 出口验证：双知识库抽查 §9.4 四判据 exit 0（cnpen/external 双跑）+反向验证零命中双向断言（脏=detected/净=zero-hits）+种子 lint 全 PASS+export 双跑 sha256 一致（确定性）+tanyin-redact --reverse-verify 进 P6 门断言真跑；探知项台账见 docs/design/2026-09-24-b5-discovery-notes.md（G-29..G-35 终态）。

