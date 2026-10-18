# 首仗点火检查单（钥匙一到即点火）· 2026-10-20

> 前提：本目录七件已备（任务卡/钥匙说明+模板/GT就位检查/能力门快照/套件基线/观察清单/本单）。红线纪律：真点火=用户点头后才执行；8900/3000/8787/8443 保留口勿占；靶场口=3081/3082。
> 变量：`<N>`=战号（续 battle-42 → 43）；`<GEN>`=代名（webui 建=G-w1 / CLI 建=自定如 G-zl1）；`<GOAL>`=~/.tanyin/battles/battle-<N>/<GEN>。

## A. 钥匙 → channels.json（用户贴钥后 3 分钟）

- [ ] A1 用户贴钥（仅此一步须用户）：把真钥交给操作员（或亲自执行 A2）
- [ ] A2 模板进位：`cp docs/runbook/channels.template.json /tmp/channels.json && chmod 600 /tmp/channels.json`（逐道把 api_key 占位符整串换真钥——形状/后端对应见 channels-key-placement.md）
- [ ] A3 形状自检：`python3 -c "import json;cs=json.load(open('/tmp/channels.json'));assert cs and all(c.get('api_key') and 'YOUR_API_KEY_HERE' not in c['api_key'] for c in cs);print('OK %d道'%len(cs))"`
- [ ] A4 泄漏防线确认：`cd /Users/wgen/redteam-agent && git status --porcelain | grep -c channels` → 期望 0（真钥永不入 git）

## B. 靶场复活 + 验活（免费，详细见 docs/FIRST-BATTLE-RUNBOOK.md 第一步）

- [ ] B1 起服（ZhuLong 仓根）：`NODE_OPTIONS="--require /tmp/zl-loopback-shim.cjs" ZL_PORT=3081 ZL_DATA_DIR=/tmp/zl-demo-data pnpm --filter @zhulong/server start`（后台）
- [ ] B2 验活：`curl -s http://127.0.0.1:3081/api/health` → ok=true；`lsof -nP -iTCP:3081 -sTCP:LISTEN` → 只见 127.0.0.1
- [ ] B3 首管+登录（首次）：`curl -X POST .../api/setup` 一次 + `curl -o /dev/null -w '%{http_code}' -X POST .../api/auth/login` → 200

## C. 点火前预检复跑（对照本目录快照，免费）

- [ ] C1 能力门：`python3 scripts/capability_gate.py` → rc=0（对照 precheck-capability-gate.md；基线锚缺口是否 --update-baseline 按母舰裁决执行）
- [ ] C2 套件复跑：`python3 -m unittest discover -s tests 2>&1 | tail -3` → 对照 precheck-suite-baseline.md（3529/71F/8E/2S），**新增引擎面红须归因后才继续**
- [ ] C3 引擎面专项：`python3 -m unittest tests.test_first_battle_readiness tests.test_gt_registry tests.test_warrior_main 2>&1 | tail -2` → OK
- [ ] C4 GT 代卷就位（若未产）：照 gt-exam-readiness.md §三产卷并覆盖 `~/.tanyin/gt/<GEN>.json`；`python3 -c "import json;json.load(open('$HOME/.tanyin/gt/<GEN>.json'));print('GT OK')"`
- [ ] C5 空转演练：`rm -rf /tmp/drydemo && cp -R demos/DEMO-1 /tmp/drydemo && python3 -m cli.warrior --goal-dir /tmp/drydemo --battle-name DEMO-1 --max-intents 1 --dry-run >/dev/null 2>&1; echo $?` → 0（本舰 2026-10-20 已复验 rc=0）
- [ ] C6 预算双保险：`export TANYIN_BATTLE_BUDGET_CAP_USD=<用户点火时定数>`（机械折算式见任务卡§四）

## D. 建仗 battle-new（两条路择一；范围/红线/预算内容=任务卡）

- [ ] D1a 【webui 路】8900 驾驶舱「新建任务」=POST /api/battle/new（授权八问真件必填，自动编号 battle-<N>、gen=G-w1、add-goal+add-scope 回执全绿才算立）
- [ ] D1b 【CLI 路】`python3 scripts/battle.py init --n <N> --gen <GEN> --brief <战书文件路径>`（注意 --brief 是**文件路径**非自由文本）→ 手工 `add-goal/add-scope` 改 127.0.0.1:3081 + 预算 500000;20000;4 + 授权八问（tanyin-ledger 命令，同 RUNBOOK 第二步）
- [ ] D2 错卷覆盖：init 已自动把 docker GT 拷到 `~/.tanyin/gt/<GEN>.json`——用 C4 代卷**覆盖之**（battle.py:38-40 拷贝源=tests/range/ground-truth.json，对 ZhuLong 是错卷）
- [ ] D3 立仗验收：`python3 cli/tanyin-ledger verify-chain --goal-dir <GOAL>` → PASS；`cat <GOAL>/goals.tsv` 八问/target/budget 逐项对任务卡

## E. 点火（真花钱，用户明确批准后）

- [ ] E1 真点火：`python3 -m cli.warrior --goal-dir <GOAL> --battle-name battle-<N> --max-intents 8 --channels /tmp/channels.json --token-cap 500000`（后台；三战士并发/240min 窗按任务卡§四）
- [ ] E2 首发验道：`tail -5 <GOAL>/timeline.tsv` 看 llmpool 首条 LLM 事件——400/401=钥形/余额问题即停归因
- [ ] E3 紧急停通路演练（开仗 10 分钟内一次）：`curl -X POST http://127.0.0.1:8900/api/battle/control -d '{"battle":<N>,"action":"pause"}'` → pause 成功后 resume（stop 面=killpg+EXIT 在册）

## F. 盯盘观察（口径全在 first-battle-observation-plan.md，禁手工调数）

- [ ] F1 只读投影盯盘：驾驶舱四问页/实时页（禁轮询写面——观测写放大教训）
- [ ] F2 预算预警：消耗过帽 80% 即记观察行（四问消费面 80% 线）
- [ ] F3 过程留痕抽查：`grep -c 'add-finding' <GOAL>/timeline.tsv` / `grep -c 'replay-probe' <GOAL>/timeline.tsv` 与 findings.tsv/replay/ 对账一次

## G. 收仗（判卷三件+七指标）

- [ ] G1 链完整：`python3 cli/tanyin-ledger verify-chain --goal-dir <GOAL>` → PASS 跳门=0
- [ ] G2 收敛结算：`python3 scripts/battle.py settle --n <N> --gen <GEN>`（**必带 --gen**——缺省 G-r1 会找错目录）
- [ ] G3 判卷（代卷）：`python3 tests/eval_range_recall.py --session <GOAL> --ground-truth ~/.tanyin/gt/<GEN>.json`
- [ ] G4 复放总账：`python3 cli/tanyin-ledger replay-summary --goal-dir <GOAL>`（C1/C2 义务 pending=0 才算误报0验证闭环）
- [ ] G5 链式面（可选）：`python3 evals/gt/gt_verify.py --live`（ZhuLong 仓只读实跑）+ `python3 evals/gt/gt_eval.py --chain evals/gt/battlefields/zl-chain-v1.json`
- [ ] G6 七指标出表：照 observation-plan §一逐行机械取数（意图/发现/复放/误报0/每意图成本/注入命中/复验触发）

## H. 蒸馏回灌（飞轮半边，仗打完 24h 内）

- [ ] H1 复盘卡：RT-0025 起（每仗归因核验，knowledge/retros/）
- [ ] H2 误报教训→哨兵回流草稿（K6 通道）+ 新打法卡草稿→人审（蒸馏管线，卡带战绩）
- [ ] H3 capability 曲线落点：判分入册 + 基线锚（若母舰裁了 --update-baseline 则此刻挂锚；否则记「首点即锚」）
- [ ] H4 战账归档：battle-<N> 目录完整保留（会话即对象范式——死会话可翻可续派）

## 点火门槛一句话

引擎面零红（C3）+ 代卷就位（C4）+ 钥匙进位（A）+ 用户批准（E）——四者齐即点火；79 红全是 UI 舰 WIP+环境病（见 precheck-suite-baseline.md §二），不阻塞但母舰已知悉。
