# 批次 4（引擎层）实施计划 —— web-blackbox 四段 / vuln-agent 适配器 / nuclei adopt / session-viz / 身份矩阵差分 / POC 重放门 / 侦察完备性

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付探隐 v2 引擎层（§11 批次 4 行）：web-blackbox 四段 skill 引擎、vuln-agent cli 适配器、nuclei adopt（模板钉 commit+ECDSA 验签）、session-viz 投影、身份矩阵差分子流程、POC 独立重放门三态、assets.type 扩 pivot/foothold+词表扩展，并落地侦察侧完备性（A1-A8 引擎位/侦察金丝雀 G-13/触发器闭包审计）。

**Architecture:** 引擎不写账本（单写者不变）：skill 型引擎=engines/ 下方法论 md（LLM 子代理按段执行），cli 型引擎=适配器进程（归一化产物为 submission.json），projector 型=只读投影。确定性部分（重放驱动/验签/投影/差分投影）进 cli/ 工具箱，攻击决策与漏洞语义判定仍禁入 CLI（铁律 7）。批次 4 前三裁决（G-2/G-12/G-13）按本计划「前置裁决」节落地，契约变更一律走微版本勘误通道。

**Tech Stack:** python3 ≥3.9 标准库（零三方运行时依赖）；ECDSA 验签经 tools.lock 锁定的 openssl 子进程；unittest + 黄金回归（tests/run_golden.py）+ 双平台 CI（windows/ubuntu × py3.11/3.12）。

**Spec:** docs/design/2026-09-21-tanyin-v2-design.md（§11 批次 4 行+§6 引擎契约+§6.6 身份矩阵+§4.8/§4.10/§4.11+§5.2 P4+§9.1/§9.2）；docs/design/2026-09-24-completeness-recon-knowledge-evolution.md（资产宇宙 A1-A8/多源法定/触发器闭包/侦察金丝雀/分母就绪门）；docs/design/2026-09-24-b3-discovery-notes.md（G 台账：G-2/G-12/G-13 批 4 前必裁决）；docs/design/2026-09-22-vuln-agent-engine.md（八段管道+结论三档）；contracts/（01/02a/03/04/06/07/08/09/10 冻结接口）。

## Global Constraints

- **仓库**：/Users/wgen/redteam-agent；**绝不碰** /Users/wgen/Documents 与 panorama/。
- **字节纪律**：UTF-8 无 BOM + LF（仓库根 .gitattributes 已钉 *.md/*.py/*.tsv/*.norm 等；新文本文件写盘一律 `encoding="utf-8", newline="\n"`）。
- **运行时**：python3 ≥3.9 标准库零三方依赖；加密原语经 openssl 子进程（tools.lock 键，python3 stdlib 无 ECDSA——契约 10 终审先例）。
- **Windows 等价**：新 CLI 入口必配 `<名>.cmd` 包装（内容=`py -3` 调用，见 cli/tanyin-ledger.cmd 先例）；测试入口一律 `[sys.executable, <脚本路径>, ...]`；控制台启动重配 UTF-8（`ensure_utf8_stdio()`）。
- **41 命令面冻结**：本批零新增账本命令；任何签名/拒收条件语义变更走**微版本勘误通道**（零存量数据期，schema_version 不递增）+ contracts/README.md 勘误索引登记（G-1/G-6/G-10 先例）。
- **铁律 7**：攻击决策/假设生成/漏洞语义判定禁入 CLI；tanyin-replay 与 tanyin-egress 是仅有的两个可对外请求的 CLI（授权窗口+scope ACL 约束内）。
- **TDD**：每任务先写失败测试→跑红→最小实现→跑绿→commit；commit 消息中文、格式「批次4 T<N>：<内容>」。
- **测试与回归**：`python3 -m unittest discover -s tests` 全绿；`python3 tests/run_golden.py` 零漂移（缺金样默认 FAIL；有意刷新/`--bless` 建档须在任务内声明——金样刷新=有意行为变更的证据）。
- **退出码对齐 Strix**：0=通过 / 1=门禁失败（REJECT，零落账）/ 2=用法或环境问题（可重跑）。
- **HANDOFF 记账**：每任务完成后在 docs/HANDOFF.md「开发流水」追加一行（日期｜子代理 T<N>｜动作+证据｜commit）。

---

## 前置裁决（批 4 前必办三件 + 本计划补充裁决）

### 裁决 A：G-2 新资产子矩阵行铸造（按 T2 预批维持原案）

- **方案**：**不新增 mint 命令**（41 面零增），`matrix-set` 放行 reason 前缀 `submatrix:` 的新键行。放行条件四合一：①行键不存在于 matrix.tsv 任何既有行；②reason 以 `submatrix:` 开头；③基线已冻结（存在 frozen_at 非空行——submatrix 语义只存在于冻结后）；④attack_surface 为**全新表面**（不出现在任何既有行键——防主矩阵偷扩张）。
- **铸造语义**：命中放行条件时**原子铸造该新表面×VOCAB 词表全集行**（约 12 行：目标行取 --state/--reason/--intent-id，其余行 state 空、reason=`submatrix:`）——分母诚实：新表面全词表立即进入闭合率分母，杜绝"少铸行刷闭合率"；全量校验后一次写入（写前拒收纪律）。
- **前缀归类规则修正（随本裁决一并落地）**：现行实现"reason 前缀与行类别不符=REJECT"会阻塞任何未归类格的**首次归类**（init 行 reason 为空→设 authz-diff: 前缀即 REJECT——身份矩阵差分根本无法落格，潜伏 bug）。修正为：**旧前缀为空→任意前缀放行（首次归类）；旧前缀非空且≠新前缀→REJECT（防串类）**。
- **authz-diff: 前缀边界**：仍限主矩阵既有键（差分落标准格，设计 §4.10）；新表面上的鉴权观察以 `submatrix:` 前缀落格（差分语义由 intent kind=authz-diff+E-index pair_group 承载，不依赖矩阵前缀）。
- **契约落点**：contracts/02a §12 matrix-set 拒收条件行改写（微版本勘误）+ P3.md 回边行对齐（见 T14）。

### 裁决 B：G-12 assets.type 词表扩展（契约微版本）

- **方案**：type 枚举九值→**十一值**：新增 `cloud-storage`（A5 存储与云：对象桶/数据库暴露/队列/云元数据端点/CDN 源站）与 `human-factor`（A7 人的因素：邮箱/账号名/泄露库命中/第三方 SSO 依赖/供应商入口）。细分**不进枚举**、落 meta（`meta=sub:object-bucket|database|queue|cloud-metadata|cdn-origin|email|account|leaked-credential|sso|vendor-portal`）——词汇表小而稳（设计 §4.8 边词汇同精神）。
- **pivot/foothold 同批启用**（§4.8"后两类批次 4 启用"）：删 add-asset 的批次 4 前拒收分支；attack 边承载链式语义不变。
- **契约落点**：contracts/01 assets.type 枚举行 + contracts/07 submission assets[].type 同步 + contracts/02a §8 add-asset 拒收条件 + phases/PROTOCOL.md §4 类映射补两行（cloud-storage→A5、human-factor→A7）——全部微版本勘误。

### 裁决 C：G-13 诱饵召回率载体（侦察金丝雀，分母就绪门第②关补全）

- **方案**：执法 canary（界外诱饵拦截零容忍）与侦察金丝雀（界内诱饵召回度量）**同工具分表**：`tanyin-canary recon-deploy` 登记客户配合植入的界内诱饵（`canary/recon-decoys.tsv`：type/value/planted_at/note），`tanyin-canary recon-recall` 机械比对诱饵表×assets.tsv 出召回率（found/planted）；`tanyin-phases denominator-ready` 增**第④断言**：planted>0 时 found==planted 否则 FAIL；planted=0 时须有披露 fact（`target=canary:recon`）在场否则 FAIL（完备性 §1.3②"100%（或披露）"语义）。
- **契约落点**：PROTOCOL §4 勘误补记（三断言→四断言）+ 契约 09 tanyin-canary 参数语义注记（G-8 待办一并清账：deploy/probe 干跑口径）。

### 补充裁决（本计划起草期发现，随对应任务落地）

| # | 裁决 | 依据 |
|---|---|---|
| R1 | **matcher 子集 v1 冻结**：`expected.matchers` 仅 {type:word,words[],condition:or\|and} 与 {type:status,status[]}；`extractors` 仅 {type:regex,name,regex[]}；多 matcher 语义=**全部命中**（AND）；未知 type=REJECT（fail-closed）。契约 06 微版本勘误补记（探知项 G-17）。 | 契约 06"schema 以 nuclei matcher 为范本"无精确子集；重放驱动需确定性可金样化 |
| R2 | **tanyin-replay 执行模型**：不 shell-exec repro_command（注入面+凭据进 argv）；v1 自解析 EV 卡片 raw_request（HTTP 报文文本）经 http.client 直发，占位符在进程内解密替换（真值不进 argv/不落盘）；scope 门链（deny-list 不适用→host 匹配 include/exclude→timeline 记 request: 事件）。repro_command 仍留人类第三方复现用。 | 铁律 7 例外条款（授权窗口+scope ACL）；四关卡①执行点回注 |
| R3 | **三态判定映射**：连接层失败（DNS/拒连/超时/SSL）=**环境差异**（REPAIRED 候选：修复卡片环境前置条件后重放）；有响应且 matcher 全中=**可复现**（VERIFIED）；有响应且 matcher 不中=**不可复现**（REJECTED）；无 matcher=manual（人工判定，退出 0 带告警）。 | §5.2 back_edges REPAIRED 语义+用户口径"可复现/不可复现/环境差异" |
| R4 | **session-viz v1 渲染**：零依赖 SVG+vanilla JS 交互（确定性分层布局，字节级可金样）；Cytoscape.js vendor 大文件留批次 6 期裁决（探知项 G-21）。视图清单（统计栏/Pipeline 时间轴/图谱十边样式/右面板/身份矩阵投影）全保留=硬语义；渲染库是实现细节。 | §6.5"Cytoscape.js 离线自包含 HTML"——离线自包含+单文件可发送是硬约束；金样确定性+无网络安装优先 |
| R5 | **authz-diff 候选直达 pending**：add-intent 直达 pending 条件扩为 `origin=recon-event 或 kind=authz-diff`（cred-obtained 事件处理器语义，设计 §6.6 步 1"直接 pending 不打分"）；契约 02a §3 微版本勘误。 | 现仅 origin=recon-event 直达（write_cmds.py:389） |
| R6 | **差分对数上限**：模块常量 `AUTHZ_DIFF_PAIR_CAP=24`（每端点含 anonymous 对照）+`--cap` 覆盖（evals 可重放）；契约 v3 回注（G-3 同型，探知项 G-20）。 | §6.6 步 1"单端点差分对数上限护栏"参数无源 |

---

## 文件结构图（每文件一职责；★=本批新增）

```
contracts/                          （只誊不创；本批全部走微版本勘误+文末勘误补记）
  01-ledger-schema.md               [改] assets.type 十一值勘误（裁决 B）
  02a-command-signatures-draft.md   [改] §3 add-intent 直达 pending/§8 add-asset 枚举/§12 matrix-set 铸行（裁决 A/B/R5）
  04-phases.md                      [改] P4 断言 5 expect 文本去 SKIP（T3）
  06-evidence-cards.md              [改] matcher 子集补记（R1/G-17）
  07-submission.md                  [改] assets[].type 同步+nday-verify 段映射注记（G-18）
  README.md                         [改] 勘误索引登记本批各笔
cli/
  tanyin-replay / .cmd        ★[新] POC 重放驱动（三态判定；对外请求例外#1；R2/R3）
  tanyin-viz / .cmd           ★[新] session-viz 投影载体（只读 13 表+timeline→单文件 HTML）
  tanyin-canary                     [改] +recon-deploy/recon-recall 子命令（裁决 C）
  tanyin-egress                     [改] compile 追加 timeline egress-compile 事件（T13 消费）
  tanyin-guard                      [改] vault 逻辑抽至 ledger/vault.py（单源化，行为零变更）
  ledger/cards.py            ★[新] EV/FD 卡片 front-matter 解析+TSV 同值性校验（复用 phases_engine.parse_yaml）
  ledger/matchers.py         ★[新] matcher 子集评估器（R1）
  ledger/vault.py            ★[新] vault 解密单源（guard/replay 共用；批次 6 换真加密不动接口）
  ledger/supply_chain.py     ★[新] tools.lock 加载+ECDSA 验签（openssl 子进程；nuclei/install 共用）
  ledger/authz_matrix.py     ★[新] role×endpoint 覆盖投影（viz 消费；evals 检出率 scorer 消费）
  ledger/viz_render.py       ★[新] viz 数据岛构建+HTML 模板渲染（纯函数）
  ledger/write_cmds.py             [改] _add_asset 十一值/_add_intent 直达 pending/_matrix_set 铸行
  ledger/phases_engine.py          [改] denominator_ready ④+trigger_audit 子命令
  README.md                        [改] 批次 4 节（tanyin-viz/tanyin-replay 交付+用法）
engines/
  web-blackbox/
    MANIFEST.md              ★[新] 引擎自述（12 字段；kind=skill）
    SKILL.md                 ★[新] 引擎路由器（≤2K token：kind→段映射/失败五类/提交纪律）
    phases/recon.md          ★[新] 段①侦察测绘+A1-A8×通道×落账引擎位表
    phases/surface.md        ★[新] 段②攻击面测绘
    phases/test.md           ★[新] 段③矩阵测试
    phases/differential.md   ★[新] 段④差分举证+身份矩阵差分五步+三条机械规则
    patterns/submission-ok.md     ★[新] 提交合格样例（含 authz finding 模板）
    patterns/submission-reject.md ★[新] 打回纠错模式
  vuln-agent/
    MANIFEST.md              ★[新] kind=cli；max_op_level=read；视角上限=L1；python3 run.py/python run.py
    adapter.py               ★[新] .vuln_agent_output→submission.json 归一化（版本→字段映射表）
  nuclei/
    MANIFEST.md              ★[新] kind=cli；max_op_level=读；视角上限=L1；验签公钥指针
    adapter.py               ★[新] 验签→guard exec 组装→JSONL→submission.json
    templates/*.yaml         ★[新] 离线模板快照（最小精选，MIT/自写）
    templates.lock           ★[新] 快照清单（upstream commit+每文件 sha256）
    README.md                ★[新] 快照来源与更新流程（钉 commit→sha256→重签）
  session-viz/
    MANIFEST.md              ★[新] kind=projector（产物不回写；载体=cli/tanyin-viz）
tools.lock                  ★[新] 供应链锁定起步版（openssl/nuclei/nuclei-templates 三键；批次 6 全量化）
phases/
  TRIGGERS.md               ★[新] 触发器目录（版本化封闭表；trigger-audit 的单源）
  PROTOCOL.md                     [改] §1 SKIP 行退役注记+§4 勘误（四断言/类映射）+§5 trigger-audit 新节
  phases.yaml                     [改] P4 断言 5 expect 文本（去"批次 4 前=SKIP"）
  P2.md P3.md P4.md               [改] 分母④/authz-diff 回边全语义/重放门强制（T14）
SKILL.md                         [改] 路由表三引擎+P3 派发引擎路由+P4 重放协议（token<2000 复测）
tests/
  test_assets_type_b4.py … test_trigger_audit.py      ★[新] 15 个测试文件（见各任务）
  eval_authz_recall.py      ★[新] 身份矩阵检出率 scorer+确定性场景（批次 6 接 LLM 在环）
  make_diff_fixture.py      ★[新] 差分样例对夹具铸造脚本（全经 CLI 命令，链自洽）
  fixtures/diff-authz/      ★[新] 差分样例对会话（正/负对）
  fixtures/engine/vuln-agent-out/ nuclei-jsonl/       ★[新] 引擎产物夹具
  fixtures/keys/            ★[新] EC 测试签名钥（TEST-ONLY 标注）
  golden/                   [改] 新增 norm 面（engine-*/viz-data/replay-envdiff 等；有意刷新面在任务内声明）
docs/design/2026-09-24-b4-discovery-notes.md ★[新] 批 4 探知项台账（G-16 起）
docs/HANDOFF.md                  [改] 开发流水记账+状态快照
```

**任务依赖**：T1→T2→(T3,T8)；T4→T5→T6；T7 独立（T8 依赖其 differential.md）；T9/T10/T11/T12/T13 相互独立（T10 依赖无）；T14 最后收口。可并行的任务组：{T3,T4,T7,T9,T10,T11,T12,T13}。

---

### Task 1: 契约勘误与 assets.type 词表扩展（裁决 B 落地）

**Files:**
- Modify: `contracts/01-ledger-schema.md`（assets.type 枚举行+文末勘误补记节）
- Modify: `contracts/07-submission.md`（assets[].type 枚举行+文末勘误补记节）
- Modify: `contracts/02a-command-signatures-draft.md`（§8 add-asset type 枚举行+文末勘误补记节）
- Modify: `phases/PROTOCOL.md`（§4 类映射补两行+勘误补记段）
- Modify: `contracts/README.md`（勘误索引登记）
- Modify: `cli/ledger/write_cmds.py:618-622`（`_add_asset` 枚举）
- Test: `tests/test_assets_type_b4.py`（新建）
- Test: `tests/test_write_cmds.py:468-477`（`test_reject_pivot_and_dup_and_enum` 改写）

**Interfaces:**
- Consumes: 契约 01/07/02a 冻结文本；write_cmds `Reject` 机制。
- Produces: assets.type 合法集=`{root-domain,subdomain,ip,service,app,endpoint,source-code,pivot,foothold,cloud-storage,human-factor}`（十一值，全批任务与引擎 md 引用此单一定义）；PROTOCOL §4 类映射含 cloud-storage→A5、human-factor→A7（T12/T13 消费）。

- [ ] **Step 1: 写失败测试**（`tests/test_assets_type_b4.py` 全文）

```python
# -*- coding: utf-8 -*-
"""批次4 T1：assets.type 十一值枚举（G-12 裁决+pivot/foothold 启用）。"""
import os, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T08:00:00Z"


def call(gd, *args):
    import subprocess
    return subprocess.run([sys.executable, CLI] + list(args) + ["--goal-dir", gd],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestAssetTypeEnum(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_pivot_foothold_now_accepted(self):
        for t, v in (("pivot", "10.10.9.9"), ("foothold", "web-01.intranet")):
            r = call(self.gd, "add-asset", "--type=" + t, "--value=" + v, "--timestamp=" + TS)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("OK", r.stdout)

    def test_new_g12_types_accepted_with_meta_sub(self):
        r = call(self.gd, "add-asset", "--type=cloud-storage", "--value=bucket-acme.s3.example.com",
                 "--meta=sub:object-bucket", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = call(self.gd, "add-asset", "--type=human-factor", "--value=cso@acme.example",
                 "--meta=sub:email", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_unknown_type_still_rejected(self):
        r = call(self.gd, "add-asset", "--type=botnet", "--value=x.example", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
```

同步改写既有 `tests/test_write_cmds.py` 的 `test_reject_pivot_and_dup_and_enum`：pivot 用例从 assert_rej 改 assert_ok（保留 dup/未知枚举两个负例，方法名改 `test_accept_pivot_and_reject_dup_and_enum`）。

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_assets_type_b4 -v`
Expected: FAIL/ERROR——pivot/cloud-storage 三例 REJECT（现行"批次 4 前启用=REJECT"与九值枚举）；未知 type 负例 PASS（既有行为）。

- [ ] **Step 3: 最小实现**

`cli/ledger/write_cmds.py` `_add_asset` 开头两段替换为：

```python
    atype = args["type"]
    # 批次4（G-12 裁决）：九值→十一值；pivot/foothold 启用（§4.8）；细分落 meta=sub:…
    if atype not in {"root-domain", "subdomain", "ip", "service", "app", "endpoint",
                     "source-code", "pivot", "foothold", "cloud-storage", "human-factor"}:
        raise Reject("type 不在十一值枚举（G-12 勘误后）: " + atype)
```

- [ ] **Step 4: 跑绿**

Run: `python3 -m unittest tests.test_assets_type_b4 tests.test_write_cmds -v` → 全 PASS。
Run: `python3 -m unittest discover -s tests` → 全绿（金样不受影响：G-g1 夹具无新 type 行）。

- [ ] **Step 5: 契约勘误落盘**（四文件，每文件文末追加"v2 勘误补记（2026-09-24·批次 4 施工期）"节）

- contracts/01：assets.type 行改 `type∈{root-domain,subdomain,ip,service,app,endpoint,source-code,pivot,foothold,cloud-storage,human-factor}`（十一值；cloud-storage/human-factor=G-12 裁决，细分落 meta=sub:…；pivot/foothold 批次 4 起启用）。
- contracts/07：assets[].type 枚举串同步（§2 数组子字段表）。
- contracts/02a §8：add-asset 拒收条件"type 不在九值枚举"改"十一值枚举（G-12 勘误）"。
- PROTOCOL §4 类映射清单补两行：`cloud-storage→A5；human-factor→A7`（原"A5/A7 无对应值"注记改指勘误后状态），并加一行勘误补记说明。
- contracts/README.md 勘误索引登记四笔。

- [ ] **Step 6: 契约自验+commit**

Run: `grep -c 'cloud-storage' contracts/01-ledger-schema.md contracts/07-submission.md phases/PROTOCOL.md` → 各 ≥1。
```bash
git add contracts/01-ledger-schema.md contracts/07-submission.md contracts/02a-command-signatures-draft.md contracts/README.md phases/PROTOCOL.md cli/ledger/write_cmds.py tests/test_assets_type_b4.py tests/test_write_cmds.py
git commit -m "批次4 T1：G-12 裁决落地——assets.type 九值→十一值（+cloud-storage/human-factor，细分落 meta=sub:）+pivot/foothold 启用（§4.8）；契约01/07/02a+PROTOCOL §4 微版本勘误四笔+README 索引登记；TDD 先红后绿（pivot/foothold/新两值正例+未知枚举负例）"
```

---

### Task 2: G-2 子矩阵行铸造（matrix-set 放行 + 前缀首次归类修正）

**Files:**
- Modify: `cli/ledger/write_cmds.py:804-844`（`_matrix_set` + `_matrix_prefix` 区）
- Modify: `contracts/02a-command-signatures-draft.md`（§12 拒收条件勘误+文末补记）
- Test: `tests/test_submatrix_mint.py`（新建）

**Interfaces:**
- Consumes: `matrix_init._load_vocab()`（VOCAB 词表加载，返回 (classes, ver, sha)）；`Ctx.append/commit/event`。
- Produces: matrix-set 新行为——①新键行铸造（裁决 A 四条件，原子铸 |VOCAB| 行）；②前缀规则=旧空→任意放行/旧非空且≠新→REJECT。timeline 事件词 `submatrix-mint <surface> classes=<n> vocab=<ver>@<sha>`（T13 trigger-audit 消费）。后续任务（T8/T13/T14）引用该事件词与铸行语义。

- [ ] **Step 1: 写失败测试**（`tests/test_submatrix_mint.py` 核心用例）

```python
# -*- coding: utf-8 -*-
"""批次4 T2：G-2 子矩阵行铸造+前缀首次归类修正（裁决 A）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T08:10:00Z"


def call(gd, *args):
    return subprocess.run([sys.executable, CLI] + list(args) + ["--goal-dir", gd],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestSubmatrixMint(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        # 夹具矩阵已初始化；先冻结基线（submatrix 语义前置）
        r = call(self.gd, "matrix-freeze", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def matrix_keys(self):
        p = os.path.join(self.gd, "matrix.tsv")
        rows = [l.split("\t") for l in open(p, encoding="utf-8").read().splitlines() if l]
        return {(r[0], r[1]): r for r in rows}

    def test_mint_new_surface_full_vocab(self):
        r = call(self.gd, "matrix-set", "--attack-surface=api2.shop.example",
                 "--vuln-class=wstg-authz", "--state=?", "--reason=submatrix: 新资产子矩阵",
                 "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        keys = self.matrix_keys()
        surf = [k for k in keys if k[0] == "api2.shop.example"]
        self.assertEqual(len(surf), 12, "新表面应铸造 VOCAB 全集 12 行，实际 %d" % len(surf))
        tgt = keys[("api2.shop.example", "wstg-authz")]
        self.assertEqual(tgt[2], "?")
        self.assertTrue(tgt[3].startswith("submatrix:"))
        other = [k for k in surf if k[1] != "wstg-authz"]
        self.assertTrue(all(keys[k][2] == "" and keys[k][3] == "submatrix:" for k in other),
                        "非目标行 state 空+reason 裸前缀")

    def test_mint_rejected_without_submatrix_prefix(self):
        r = call(self.gd, "matrix-set", "--attack-surface=api3.shop.example",
                 "--vuln-class=wstg-authz", "--state=?", "--reason=普通理由", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("submatrix:", r.stdout + r.stderr)

    def test_mint_rejected_before_freeze(self):
        gd2 = shutil.copytree(FIX, os.path.join(self.tmp, "G-nofreeze"))
        r = call(gd2, "matrix-set", "--attack-surface=api4.shop.example",
                 "--vuln-class=wstg-authz", "--state=?", "--reason=submatrix: x", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("冻结", r.stdout + r.stderr)

    def test_existing_surface_new_key_rejected(self):
        surf0 = next(iter(self.matrix_keys()))[0]
        r = call(self.gd, "matrix-set", "--attack-surface=" + surf0,
                 "--vuln-class=wstg-authz", "--state=?", "--reason=submatrix: x", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("新表面", r.stdout + r.stderr)

    def test_first_categorization_authz_diff_allowed(self):
        """前缀首次归类修正：init 行 reason 空→authz-diff: 前缀放行（修潜伏阻塞）。"""
        keys = self.matrix_keys()
        fresh = next(k for k in keys if keys[k][3] == "" and keys[k][2] == "")
        r = call(self.gd, "matrix-set", "--attack-surface=" + fresh[0],
                 "--vuln-class=" + fresh[1], "--state=x",
                 "--reason=authz-diff: 各角色 403 一致", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_category_flip_rejected(self):
        keys = self.matrix_keys()
        fresh = next(k for k in keys if keys[k][3] == "" and keys[k][2] == "")
        call(self.gd, "matrix-set", "--attack-surface=" + fresh[0], "--vuln-class=" + fresh[1],
             "--state=x", "--reason=authz-diff: a", "--timestamp=" + TS)
        r = call(self.gd, "matrix-set", "--attack-surface=" + fresh[0],
                 "--vuln-class=" + fresh[1], "--state=x", "--reason=submatrix: b", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("前缀", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_submatrix_mint -v`
Expected: 铸行/首次归类用例 FAIL（现行"行键不存在=REJECT"+"前缀不符=REJECT"）；拒绝路径用例可能已 PASS。

- [ ] **Step 3: 最小实现**

`_matrix_set` 中 `if not key_rows: raise Reject(...)` 段整体替换：

```python
    key_rows = [r for r in rows if r[0] == args["attack-surface"] and r[1] == args["vuln-class"]]
    reason = args.get("reason", "")
    if not key_rows:
        # G-2 裁决（批4）：新键行铸造仅限 submatrix:（四条件，裁决 A）
        if not reason.startswith("submatrix:"):
            raise Reject("行键不存在且 reason 前缀非 submatrix:（不允许置格行外新键）: %s×%s"
                         % (args["attack-surface"], args["vuln-class"]))
        if not any(ctx.val("matrix.tsv", r, "frozen_at") for r in rows):
            raise Reject("子矩阵行铸造须基线已冻结（先 matrix-freeze）")
        if args["attack-surface"] in {r[0] for r in rows}:
            raise Reject("表面已存在于既有行键——非新表面，不得 submatrix: 铸造（防主矩阵偷扩张）")
        from .matrix_init import _load_vocab, DEFAULT_VOCAB
        classes, ver, vsha = _load_vocab(DEFAULT_VOCAB)
        if args["vuln-class"] not in classes:
            raise Reject("vuln_class 不在 VOCAB（WSTG 版本化全集）: " + args["vuln-class"])
        mint = []
        for vc in classes:
            tgt = (vc == args["vuln-class"])
            mint.append(_row("matrix.tsv",
                             attack_surface=args["attack-surface"], vuln_class=vc,
                             state=(state if tgt else ""), reason=(reason if tgt else "submatrix:"),
                             intent_id=(iid if tgt else ""), updated=args["timestamp"], frozen_at=""))
        for row in mint:
            ctx.append("matrix.tsv", row)
        ctx.event(args["timestamp"],
                  "submatrix-mint %s classes=%d vocab=%s@%s" % (args["attack-surface"], len(classes), ver, vsha),
                  phase=args.get("phase", ""))
        ctx.commit({"matrix.tsv", "timeline.tsv"})
        _ok_line("铸行 %s（×%d 词表全集）" % (args["attack-surface"], len(classes)), "matrix.tsv", mint)
        return 0
```

注意：原实现里 `state`/`iid` 赋值与 reason 读取须移到该段之前（重排 `state = args["state"]`、`iid = args.get("intent-id", "")`、`reason = args.get("reason", "")` 三行到 key_rows 计算后、新键分支前），后段保持不变。前缀一致性检查改为：

```python
    prev_prefix = _matrix_prefix(ctx.val("matrix.tsv", key_rows[-1], "reason))
    new_prefix = _matrix_prefix(reason)
    if prev_prefix and new_prefix != prev_prefix:   # 旧空=首次归类放行（批4修正）；旧非空≠新=REJECT
        raise Reject("reason 前缀与行类别不符（现行类别前缀=%r）: %s" % (prev_prefix, reason))
```

- [ ] **Step 4: 跑绿+回归**

Run: `python3 -m unittest tests.test_submatrix_mint tests.test_write_cmds tests.test_negative_matrix -v` → 全 PASS。
Run: `python3 tests/run_golden.py` → 零漂移（金样 matrix-set 用既有键，不走铸行分支）。
Run: `python3 -m unittest discover -s tests` → 全绿。

- [ ] **Step 5: 契约勘误+commit**

contracts/02a §12 拒收条件行追加勘误补记（文末节）："行键不存在且 reason 前缀 submatrix: 且基线已冻结且为全新表面→放行：原子铸造该表面×VOCAB 全集行（目标行取 --state/--reason/--intent-id，其余 state 空+裸前缀；timeline 事件 submatrix-mint）；reason 前缀规则修正=旧前缀空→任意前缀首次归类放行，旧前缀非空且≠新→REJECT（G-2 裁决，2026-09-24）"；contracts/README.md 索引登记。

```bash
git add cli/ledger/write_cmds.py contracts/02a-command-signatures-draft.md contracts/README.md tests/test_submatrix_mint.py
git commit -m "批次4 T2：G-2 裁决落地——matrix-set 放行 submatrix: 新键行（四条件）+原子铸造新表面×VOCAB 全集（分母诚实）+前缀首次归类修正（修 authz-diff 落格潜伏阻塞）；契约02a §12 微版本勘误；TDD 先红后绿 6 例（铸行/无前缀拒/未冻结拒/非新表面拒/首次归类放行/串类拒）"
```

---

### Task 3: P4 重放门断言转强制（SKIP 退役）

**Files:**
- Modify: `phases/phases.yaml:79`（P4 断言 5 expect 文本）
- Modify: `phases/PROTOCOL.md`（§1 判定表 SKIP 行退役注记）
- Modify: `phases/P4.md`（duty 3/4 改强制；披露义务段改历史注记）
- Modify: `contracts/04-phases.md`（P4 断言 5 行+文末勘误补记）
- Test: `tests/test_p4_gate_mandatory.py`（新建）

**Interfaces:**
- Consumes: `tanyin-phases gate --phase P4`（批次 3 T3 判定表）；`ledger-replay-summary`（既有）。
- Produces: P4 门第五断言=硬断言（C1/C2 finding 无重放态→gate-fail:P4）；T6 重放门 eval 依赖此行为；SKILL/P4.md 文字（T14）。

- [ ] **Step 1: 写失败测试**（`tests/test_p4_gate_mandatory.py`）

```python
# -*- coding: utf-8 -*-
"""批次4 T3：P4 重放门断言转强制——expect 文本去 SKIP 后 gate 不再记 skip。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PHASES_CLI = os.path.join(ROOT, "cli", "tanyin-phases")
YAML = os.path.join(ROOT, "phases", "phases.yaml")


class TestP4GateMandatory(unittest.TestCase):
    def test_yaml_expect_no_skip_marker(self):
        text = open(YAML, encoding="utf-8").read()
        self.assertNotIn("批次 4 前=SKIP", text, "P4 断言 expect 仍含 SKIP 标记（批4 已转强制）")
        self.assertIn("ledger-replay-summary", text)

    def test_protocol_retired_note(self):
        text = open(os.path.join(ROOT, "phases", "PROTOCOL.md"), encoding="utf-8").read()
        self.assertIn("已退役", text, "PROTOCOL §1 SKIP 判定行须标注已退役（2026-09-24 批4）")


if __name__ == "__main__":
    unittest.main()
```

（行为级验证在 T6：构造带未重放 C1 finding 的会话跑 `tanyin-phases gate --phase P4` 期望 gate-fail——此处先锁声明层。）

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_p4_gate_mandatory -v` → 两例 FAIL（yaml 仍含 SKIP 标记）。

- [ ] **Step 3: 最小实现**

- `phases/phases.yaml` P4 断言 5：`- {cmd: "ledger-replay-summary", expect: "无 REJECTED 未处置项"}`（删"（批次 4 前=SKIP，报告中披露）"）。
- `phases/PROTOCOL.md` §1 判定表该行行尾加注：`【已退役 2026-09-24·批4：P4 expect 文本已去 SKIP 标记，本行保留备查——历史会话 yaml 不再含该词，规则不再触发】`。
- `phases/P4.md` duty 3 改：`3. POC 独立重放门（强制）：fresh 隔离子代理只拿 EV 卡片盲重放——驱动=tanyin-replay（机械判定三态：可复现/不可复现/环境差异），落账=set-replay-state 三态（VERIFIED/REPAIRED/REJECTED；环境差异=REPAIRED 候选，修复卡片环境前置条件后重放，max_retry=2）。无 matcher 的卡片=人工判定后落态。`；duty 4 披露义务段改为：`4. 历史注记：批次 4 前该断言曾为 SKIP 并在报告披露；批4 起强制，披露义务仅适用于 REJECTED 未处置项的处置说明。`
- `contracts/04-phases.md` P4 断言 5 行同步+文末勘误补记（微版本：expect 文本变更，断言数不变=21 基线不动）。

- [ ] **Step 4: 跑绿+回归**

Run: `python3 -m unittest tests.test_p4_gate_mandatory -v` → PASS。
Run: `python3 -m unittest discover -s tests` → 全绿（干跑止于 P2 不触发 P4 门；kill9/eval 同理——若有测试构造过 P4 门 SKIP 计数，按新语义改写并在 commit 注明）。
Run: `python3 tests/run_golden.py` → `phases-validate.norm` 零漂移（validate 输出为计数型 asserts=21 不含 expect 文本；若实现有出入，属有意刷新——`--bless` 并在 commit 注明）。

- [ ] **Step 5: Commit**

```bash
git add phases/phases.yaml phases/PROTOCOL.md phases/P4.md contracts/04-phases.md tests/test_p4_gate_mandatory.py
git commit -m "批次4 T3：P4 重放门断言转强制——phases.yaml expect 去「批次 4 前=SKIP」+PROTOCOL §1 判定行退役注记+P4.md duty 强制化（tanyin-replay 驱动+三态落账协议）+契约04 微版本勘误（断言数 21 基线不动）；TDD 先红后绿 2 例"
```

---

### Task 4: EV 卡片解析器 + matcher 子集评估器 + vault 单源抽取

**Files:**
- Create: `cli/ledger/cards.py`、`cli/ledger/matchers.py`、`cli/ledger/vault.py`
- Modify: `cli/tanyin-guard`（vault 函数改调 ledger.vault，行为零变更）
- Test: `tests/test_cards_matchers.py`（新建）

**Interfaces:**
- Consumes: `phases_engine.parse_yaml`（受限 YAML 子集解析器，EV 卡片 front-matter 同构）；契约 06 EV 卡片 11 字段。
- Produces（T5/T6/T11 消费，签名冻结）：
  - `cards.parse_ev_card(path) -> dict`（11 字段全量；expected 为嵌套 dict；缺字段/格式错 raise `CardError(msg)`）
  - `cards.check_consistency(card: dict, eindex_row: list) -> list[str]`（network_position/pair_group/title 同值性违例清单，空=一致）
  - `matchers.evaluate(expected: dict, status: int, headers: dict, body: str) -> dict`（返回 `{"matched": bool, "results": [{"type","detail","ok"}], "extracted": {name: str}}`；`expected` 为空/`{}` → `{"matched": None, ...}` 表 manual）
  - `vault.load_key(gd)` / `vault.secret(gd, n) -> str` / `vault.secrets(gd) -> list[(n, str)]`（guard 现逻辑原样搬家；XOR 实现批次 6 换真加密不动签名）

- [ ] **Step 1: 写失败测试**（`tests/test_cards_matchers.py`）

```python
# -*- coding: utf-8 -*-
"""批次4 T4：EV 卡片解析+matcher 子集评估（R1）+vault 单源。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import cards, matchers  # noqa: E402

CARD = """---
id: EV-g1-0041
title: 管理接口未授权访问-实验组
source_type: command
observed_at: 2026-09-21T10:22:05+08:00
network_position: intranet
preconditions:
  - "持有有效会话 {{vault:cred-3}}"
raw_request: |
  GET /admin/api/users HTTP/1.1
  Host: app.intranet
  Cookie: {{vault:cred-3}}
expected:
  matchers:
    - {type: word, words: ["errorCode:00000"]}
    - {type: status, status: [200]}
  extractors:
    - {type: regex, name: user_count, regex: ['"total":(\\d+)']}
cleanup: ''
pair_group: PG-g1-0007
role: admin
---
## 原始响应摘录（脱敏+定长）与判定依据
200 OK errorCode:00000 "total":42
"""


class TestCards(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.p = os.path.join(tempfile.mkdtemp(), "EV-g1-0041.md")
        open(self.p, "w", encoding="utf-8", newline="\n").write(CARD)

    def test_parse_full_card(self):
        c = cards.parse_ev_card(self.p)
        self.assertEqual(c["id"], "EV-g1-0041")
        self.assertEqual(c["network_position"], "intranet")
        self.assertEqual(c["pair_group"], "PG-g1-0007")
        self.assertEqual(c["role"], "admin")
        self.assertIn("{{vault:cred-3}}", c["raw_request"])
        self.assertEqual(len(c["expected"]["matchers"]), 2)
        self.assertEqual(c["preconditions"], ["持有有效会话 {{vault:cred-3}}"])

    def test_consistency_check(self):
        c = cards.parse_ev_card(self.p)
        row = ["EV-g1-0041", "别的标题", "command", "ts", "internet", "curl -s x", "single",
               "a"*64, "b"*64, "art/1", "evidence/EV-g1-0041.md", "", "PG-g1-0007", "excerpt", "2", "ts"]
        errs = cards.check_consistency(c, row)
        self.assertEqual(len(errs), 2, "network_position+title 两处不同值: %r" % errs)


class TestMatchers(unittest.TestCase):
    EXP = {"matchers": [{"type": "word", "words": ["errorCode:00000"]},
                        {"type": "status", "status": [200]}],
           "extractors": [{"type": "regex", "name": "user_count", "regex": ['"total":(\\d+)']}]}

    def test_all_match_and_extract(self):
        r = matchers.evaluate(self.EXP, 200, {}, 'errorCode:00000 "total":42')
        self.assertTrue(r["matched"])
        self.assertEqual(r["extracted"]["user_count"], "42")

    def test_word_miss(self):
        r = matchers.evaluate(self.EXP, 200, {}, 'errorCode:1 "total":42')
        self.assertFalse(r["matched"])

    def test_status_miss(self):
        r = matchers.evaluate(self.EXP, 403, {}, 'errorCode:00000')
        self.assertFalse(r["matched"])

    def test_word_condition_or(self):
        exp = {"matchers": [{"type": "word", "words": ["a", "b"], "condition": "or"}]}
        self.assertTrue(matchers.evaluate(exp, 200, {}, "只有 b")["matched"])

    def test_unknown_type_rejected(self):
        with self.assertRaises(matchers.MatcherError):
            matchers.evaluate({"matchers": [{"type": "dsl", "dsl": "x"}]}, 200, {}, "")

    def test_empty_expected_is_manual(self):
        r = matchers.evaluate({}, 200, {}, "body")
        self.assertIsNone(r["matched"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_cards_matchers -v` → ERROR（模块不存在）。

- [ ] **Step 3: 最小实现**

`cli/ledger/cards.py`：

```python
# -*- coding: utf-8 -*-
"""EV/FD 卡片 front-matter 解析+TSV 同值性（契约 06；批4 T4）。

受限 YAML 子集复用 phases_engine.parse_yaml（块映射/列表/行内流/块标量全覆盖）。
双轨规则（§4.11）：标量 TSV 列为权威，卡片复核同值——不一致=P4 校验失败。"""


class CardError(Exception):
    pass


def parse_ev_card(path):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---"):
        raise CardError("卡片缺 front-matter 起始定界: " + path)
    parts = text.split("\n---\n", 1)
    if len(parts) != 2 or not parts[0][3:].strip():
        raise CardError("front-matter 未闭合或为空: " + path)
    from .phases_engine import parse_yaml, PhasesSyntaxError
    try:
        fields = parse_yaml(parts[0][3:])
    except PhasesSyntaxError as e:
        raise CardError("front-matter 语法错误: %s (%s)" % (e, path))
    if not isinstance(fields, dict) or "id" not in fields:
        raise CardError("front-matter 非 mapping 或缺 id: " + path)
    for k in ("network_position", "pair_group"):
        if k in fields and not isinstance(fields[k], str):
            raise CardError("%s 须为标量: %r" % (k, fields[k]))
    return fields


def check_consistency(card, eindex_row):
    from .schemas import TABLES
    cols = TABLES["E-index.tsv"]
    errs = []
    for card_key, col in (("id", "id"), ("title", "title"),
                          ("network_position", "network_position"),
                          ("pair_group", "pair_group")):
        cv = card.get(card_key, "")
        tv = eindex_row[cols.index(col)] if col in cols else ""
        if cv and tv and cv != tv:
            errs.append("%s 不同值: 卡片=%r TSV=%r" % (card_key, cv, tv))
    return errs
```

`cli/ledger/matchers.py`：

```python
# -*- coding: utf-8 -*-
"""matcher 子集评估器（R1/G-17；契约 06 微版本勘误）。

子集：word（words[]+condition or|and，默认 and）/ status（status[]）/ regex extractor；
多 matcher 语义=全部命中（AND）；未知 type raise MatcherError（fail-closed）。"""


class MatcherError(Exception):
    pass


def _word(m, body):
    words = m.get("words")
    if not isinstance(words, list) or not words:
        raise MatcherError("word matcher 缺 words[]: %r" % m)
    cond = m.get("condition", "and")
    if cond not in ("and", "or"):
        raise MatcherError("word condition 仅 and|or: %r" % cond)
    if cond == "or":
        return any(w in body for w in words)
    return all(w in body for w in words)


def _status(m, status):
    st = m.get("status")
    if not isinstance(st, list) or not st:
        raise MatcherError("status matcher 缺 status[]: %r" % m)
    return status in [int(x) for x in st]


def evaluate(expected, status, headers, body):
    """expected={}→matched=None（manual：无 matcher 无法机械判定）。"""
    if not expected or not expected.get("matchers"):
        return {"matched": None, "results": [], "extracted": {}}
    results, ok_all, extracted = [], True, {}
    for m in expected.get("matchers", []):
        t = m.get("type")
        if t == "word":
            ok = _word(m, body)
            results.append({"type": "word", "detail": m.get("words"), "ok": ok})
        elif t == "status":
            ok = _status(m, status)
            results.append({"type": "status", "detail": m.get("status"), "ok": ok})
        else:
            raise MatcherError("matcher type 不在子集 {word,status}: %r" % t)
        ok_all = ok_all and ok
    for e in expected.get("extractors", []):
        if e.get("type") != "regex":
            raise MatcherError("extractor type 不在子集 {regex}: %r" % e.get("type"))
        import re
        pats = e.get("regex") or []
        if not isinstance(pats, list) or not pats:
            raise MatcherError("regex extractor 缺 regex[]: %r" % e)
        mo = re.search(pats[0], body)
        if mo:
            extracted[e.get("name", "")] = mo.group(1) if mo.groups() else mo.group(0)
    return {"matched": ok_all, "results": results, "extracted": extracted}
```

`cli/ledger/vault.py`：把 `cli/tanyin-guard` 内 `vault_dir/_load_key/_decrypt/vault_secrets` 四函数原样搬入（命名 `load_key/secret/secrets`），`tanyin-guard` 改 `from ledger import vault` 调用（sys.path 已插入）；`cli/tanyin-guard` 对应函数体改 thin delegate 保持命令行为与输出字节不变。

- [ ] **Step 4: 跑绿+回归**

Run: `python3 -m unittest tests.test_cards_matchers tests.test_guard -v` → 全 PASS（guard 行为零变更由既有 guard 测试背书）。
Run: `python3 -m unittest discover -s tests` + `python3 tests/run_golden.py` → 全绿零漂移。

- [ ] **Step 5: 契约勘误+commit**

contracts/06 文末勘误补记：matcher 子集 v1（R1 全文照前置裁决表）；contracts/README 索引登记。

```bash
git add cli/ledger/cards.py cli/ledger/matchers.py cli/ledger/vault.py cli/tanyin-guard contracts/06-evidence-cards.md contracts/README.md tests/test_cards_matchers.py
git commit -m "批次4 T4：EV 卡片解析器（parse_yaml 复用+同值性校验）+matcher 子集评估器（word/status/regex+AND 语义+fail-closed）+vault 单源抽取（guard/replay 共用，行为零变更）；契约06 matcher 子集微版本勘误（G-17）；TDD 先红后绿 9 例"
```

---

### Task 5: tanyin-replay 重放驱动（三态判定）

**Files:**
- Create: `cli/tanyin-replay`、`cli/tanyin-replay.cmd`
- Test: `tests/test_replay_driver.py`（新建）
- Test/Golden: `tests/run_golden.py`（ENGINE_CMDS 段新增 replay 面）

**Interfaces:**
- Consumes: T4 `cards.parse_ev_card/check_consistency`、`matchers.evaluate`、`vault.secret`；`write_cmds._match_value`（scope 匹配）；`core.Session`（E-index/timeline 读写）。
- Produces（T6/T14 消费）：
  - `tanyin-replay replay --goal-dir D --id=EV-xxx [--scheme=http|https] [--port=N] [--timeout=10] [--timestamp=T]` → stdout JSON：`{"id","verdict","matched","status","results","extracted","suggest","detail"}`；verdict∈{reproduced,not-reproduced,env-diff,manual}；suggest=`set-replay-state` 建议命令行（env-diff→REPAIRED 候选附 note）。退出码 0=判定完成 / 1=执法或校验拒绝 / 2=用法。
  - `tanyin-replay matcher-test --expected-file P --response-file F`（离线评估：REPAIRED 修复循环与测试用）。
  - timeline 事件：每请求 `request: <host><path> via=replay`（§4.10 对外请求记账）+ 判定 `replay-probe <EV-id> verdict=<v>`。
  - 判定产物：`<goal-dir>/replay/<EV-id>/<seq>.json`（只增不覆盖，seq=目录内现序号+1）。

- [ ] **Step 1: 写失败测试**（`tests/test_replay_driver.py`）

```python
# -*- coding: utf-8 -*-
"""批次4 T5：tanyin-replay 驱动——三态判定（R2/R3）+scope 门链+request 记账。"""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REPLAY = os.path.join(ROOT, "cli", "tanyin-replay")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T09:00:00Z"


def run(*args):
    return subprocess.run([sys.executable] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def first_ev(self):
        p = os.path.join(self.gd, "E-index.tsv")
        return [l.split("\t") for l in open(p, encoding="utf-8").read().splitlines() if l][0][0]


class TestReplayDriver(Base):
    def test_env_diff_on_connection_refused(self):
        ev = self.first_ev()
        r = run(REPLAY, "replay", "--goal-dir", self.gd, "--id=" + ev,
                "--scheme=http", "--port=1", "--timeout=2", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        j = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(j["verdict"], "env-diff")
        self.assertIn("REPAIRED", j["suggest"])

    def test_reject_out_of_scope_host(self):
        ev = self.first_ev()
        card = os.path.join(self.gd, "evidence", ev + ".md")
        open(card, "w", encoding="utf-8", newline="\n").write(
            "---\nid: %s\nnetwork_position: internet\nraw_request: |\n  GET /x HTTP/1.1\n"
            "  Host: evil.outside\nexpected: {}\npair_group: \n---\n## 摘\n" % ev)
        r = run(REPLAY, "replay", "--goal-dir", self.gd, "--id=" + ev,
                "--scheme=http", "--timeout=2", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("scope", (r.stdout + r.stderr).lower())

    def test_unknown_id_exit_two(self):
        r = run(REPLAY, "replay", "--goal-dir", self.gd, "--id=EV-g1-9999")
        self.assertEqual(r.returncode, 2)

    def test_matcher_test_offline(self):
        exp = os.path.join(self.tmp, "exp.json")
        resp = os.path.join(self.tmp, "resp.txt")
        open(exp, "w", encoding="utf-8").write(json.dumps(
            {"matchers": [{"type": "status", "status": [200]}]}))
        open(resp, "w", encoding="utf-8").write("HTTP/1.1 200 OK\r\n\r\nok")
        r = run(REPLAY, "matcher-test", "--expected-file", exp, "--response-file", resp)
        self.assertEqual(r.returncode, 0)
        self.assertIn("\"matched\": true", r.stdout)


if __name__ == "__main__":
    unittest.main()
```

（G-g1 夹具 E-index 首行的 network_position/pair_group 与其卡片一致——add-evidence 生成时已同值；test_reject_out_of_scope_host 重写卡片 Host=evil.outside 触发界外。）

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_replay_driver -v` → ERROR（脚本不存在/入口 2）。

- [ ] **Step 3: 最小实现**（`cli/tanyin-replay` 骨架全文）

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tanyin-replay（批次 4 T5）——POC 独立重放驱动（铁律 7 对外请求例外#1）。

replay：EV 卡片盲重放——解析 raw_request（HTTP 报文文本）→{{vault:cred-N}} 进程内解密替换
（真值不进 argv/不落盘，R2）→host 过 scope include/exclude（出界=REJECT exit 1）→http.client
直发→matcher 评估→三态（R3）：连接层失败=env-diff（REPAIRED 候选）/全中=reproduced
（VERIFIED）/不中=not-reproduced（REJECTED）/无 matcher=manual。
每请求落 timeline request: 事件（§4.10）；判定产物 replay/<EV-id>/<seq>.json 只增不覆盖。
matcher-test：离线评估（REPAIRED 修复循环）。退出码 0/1/2 对齐 Strix。"""
import http.client, json, os, re, socket, ssl, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ledger import cards, core, matchers, vault  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402
from ledger.core import ensure_utf8_stdio  # noqa: E402

ensure_utf8_stdio()
TAB = chr(9)
EPOCH = "1970-01-01T00:00:00Z"
PLACEHOLDER = re.compile(r"\{\{vault:cred-(\d+)\}\}")
REQUEST_LINE = re.compile(r"^([A-Z]+) (\S+) HTTP/(1\.[01])$")
SUGGEST = {"reproduced": "VERIFIED", "not-reproduced": "REJECTED", "env-diff": "REPAIRED"}


def usage():
    sys.stderr.write("用法: tanyin-replay replay --goal-dir D --id=<EV-id> [--scheme=http|https]"
                     " [--port=N] [--timeout=10] [--timestamp=T]"
                     " | matcher-test --expected-file P --response-file F" + chr(10))
    return 2


def parse_raw_request(text):
    lines = text.splitlines()
    m = REQUEST_LINE.match(lines[0].strip())
    if not m:
        raise ValueError("raw_request 首行非请求行: %r" % lines[0])
    headers, body, i = {}, [], 1
    for ln in lines[1:]:
        if not ln.strip():
            i += 1
            break
        k, _, v = ln.partition(":")
        headers[k.strip().lower()] = v.strip()
        i += 1
    body = "\r\n".join(lines[i:])
    return m.group(1), m.group(2), headers, body


def append_tl(gd, ts, event):
    s = core.Session(gd)
    rows = s.rows("timeline.tsv")
    hi = TABLES["timeline.tsv"].index("hash")
    prev = rows[-1][hi] if rows else core.GENESIS
    wo = [ts, "replay", "P4", event, "", prev, "2"]
    rows.append([ts, "replay", "P4", event, "", prev, core.row_hash(prev, wo), "2"])
    core.write_tsv(os.path.join(gd, "timeline.tsv"), rows)


def host_in_scope(gd, host):
    from ledger.write_cmds import _match_value
    s = core.Session(gd)
    hit = False
    fi = TABLES["scope.tsv"].index("amendment_of")
    superseded = {r[fi] for r in s.rows("scope.tsv") if r[fi]}
    for r in s.rows("scope.tsv"):
        if r[0] in superseded:
            continue
        kind = r[TABLES["scope.tsv"].index("kind")]
        if kind not in ("include", "exclude"):
            continue
        if _match_value(host, r[TABLES["scope.tsv"].index("matcher")]):
            if kind == "exclude":
                return False
            hit = True
    return hit


def cmd_replay(gd, rest):
    kv = dict(a.partition("=")[::2] for a in rest if a.startswith("--"))
    rid = kv.get("--id", "")
    if not rid or not rid.startswith("EV-"):
        return usage()
    s = core.Session(gd)
    row = next((r for r in s.rows("E-index.tsv") if r[0] == rid), None)
    if row is None:
        sys.stderr.write("REJECT\treplay\t--id 引用闭合失败（E-index 无此行）: %s\n" % rid)
        return 1
    card_path = os.path.join(gd, row[TABLES["E-index.tsv"].index("card_path")])
    try:
        card = cards.parse_ev_card(card_path)
    except cards.CardError as e:
        sys.stderr.write("REJECT\treplay\t卡片不可解析: %s\n" % e)
        return 1
    errs = cards.check_consistency(card, row)
    if errs:
        sys.stderr.write("REJECT\treplay\t卡片与 E-index 同值性失败（§4.11）: %s\n" % "; ".join(errs))
        return 1
    raw = card.get("raw_request", "") or ""
    if not raw.strip():
        sys.stderr.write("REJECT\treplay\traw_request 空——无可重放请求\n")
        return 1
    method, path, headers, body = parse_raw_request(raw)
    host = headers.get("host", "")
    if not host:
        sys.stderr.write("REJECT\treplay\traw_request 缺 Host 头\n")
        return 1
    if ":" in host:
        host, _, port_s = host.partition(":")
        port = int(port_s) if port_s.isdigit() else (443 if kv.get("--scheme") == "https" else 80)
    else:
        port = int(kv.get("--port", "0") or 0) or (443 if kv.get("--scheme") == "https" else 80)
    if not host_in_scope(gd, host):
        append_tl(gd, kv.get("--timestamp", EPOCH), "request: %s%s via=replay REJECT=out-of-scope" % (host, path))
        sys.stderr.write("REJECT\treplay\t目标 host 界外（scope include/exclude 判定）: %s\n" % host)
        return 1
    # 占位符进程内回注（四关卡①：真值不进 argv/不落盘）
    def sub(mo):
        return vault.secret(gd, mo.group(1))
    headers = {k: PLACEHOLDER.sub(sub, v) for k, v in headers.items()}
    body = PLACEHOLDER.sub(sub, body)
    append_tl(gd, kv.get("--timestamp", EPOCH), "request: %s%s via=replay" % (host, path))
    scheme = kv.get("--scheme", "http")
    timeout = float(kv.get("--timeout", "10"))
    try:
        conn_cls = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
        conn = conn_cls(host, port, timeout=timeout)
        conn.request(method, path, body=body or None, headers=dict(headers))
        resp = conn.getresponse()
        status, rheaders, rbody = resp.status, dict(resp.getheaders()), resp.read().decode("utf-8", "replace")
        conn.close()
    except (socket.error, ssl.SSLError, OSError, http.client.HTTPException) as e:
        verdict, out = "env-diff", {"matched": None, "results": [], "extracted": {},
                                    "detail": "%s: %s" % (type(e).__name__, e)}
    else:
        ev = matchers.evaluate(card.get("expected") or {}, status,
                               {k.lower(): v for k, v in rheaders.items()}, rbody)
        verdict = {True: "reproduced", False: "not-reproduced", None: "manual"}[ev["matched"]]
        out = {"matched": ev["matched"], "status": status, "results": ev["results"],
               "extracted": ev["extracted"]}
    note = {"env-diff": "环境差异（连接层失败）——修复 EV 卡片 preconditions 网络位置/前置后重放"}.get(verdict, "")
    suggest = ("tanyin-ledger set-replay-state --goal-dir %s --id=%s --state=%s%s"
               % (gd, rid, SUGGEST.get(verdict, "VERIFIED"),
                  (" --note=" + note) if note else ""))
    result = {"id": rid, "verdict": verdict}
    result.update(out)
    result["suggest"] = suggest if verdict != "manual" else "无 matcher——人工判定后落态"
    d = os.path.join(gd, "replay", rid)
    os.makedirs(d, exist_ok=True)
    seq = len([x for x in os.listdir(d) if x.endswith(".json")]) + 1
    with open(os.path.join(d, "%d.json" % seq), "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, ensure_ascii=False, sort_keys=True)
    append_tl(gd, kv.get("--timestamp", EPOCH), "replay-probe %s verdict=%s" % (rid, verdict))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


def cmd_matcher_test(rest):
    kv = dict(a.partition("=")[::2] for a in rest if a.startswith("--"))
    if not kv.get("--expected-file") or not kv.get("--response-file"):
        return usage()
    expected = json.load(open(kv["--expected-file"], encoding="utf-8"))
    text = open(kv["--response-file"], encoding="utf-8", errors="replace").read()
    head, _, body = text.partition("\r\n\r\n")
    status = int(head.split(" ")[1]) if len(head.split(" ")) > 1 and head.split(" ")[1].isdigit() else 0
    print(json.dumps(matchers.evaluate(expected, status, {}, body), ensure_ascii=False, sort_keys=True))
    return 0


def main(argv):
    if len(argv) < 2:
        return usage()
    sub, rest = argv[1], argv[2:]
    if sub == "replay":
        gd = next((a[12:] for a in rest if a.startswith("--goal-dir=")), "")
        if not gd:
            return usage()
        return cmd_replay(gd, [a for a in rest if not a.startswith("--goal-dir=")])
    if sub == "matcher-test":
        return cmd_matcher_test(rest)
    return usage()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

`cli/tanyin-replay.cmd`（照抄 tanyin-ledger.cmd 形态，替换脚本名）：

```bat
@echo off
py -3 "%~dp0tanyin-replay" %*
```

- [ ] **Step 4: 跑绿+金样接入**

Run: `python3 -m unittest tests.test_replay_driver -v` → 全 PASS。
`tests/run_golden.py` 增 `ENGINE_CMDS` 段（与 PHASES_CMDS 同机制；先复制 G-g1 到临时目录再跑，norm 名 `replay-envdiff.norm`）：

```python
REPLAY_CLI = os.path.join(HERE, "..", "cli", "tanyin-replay")
ENGINE_CMDS = [("replay-envdiff", [sys.executable, REPLAY_CLI, "replay", "--goal-dir", "<GD>",
                                   "--id=EV-g1-0001", "--scheme=http", "--port=1",
                                   "--timeout=2", "--timestamp=2026-09-24T09:00:00Z"])]
```

（执行器把 `<GD>` 替换为 fresh 拷贝路径；norm 归一剥 seq 文件名与端口细节——norm 内容=verdict 行。）Run: `python3 tests/run_golden.py --bless`（首建）→ 再跑一次零漂移。

- [ ] **Step 5: Commit**

```bash
git add cli/tanyin-replay cli/tanyin-replay.cmd tests/test_replay_driver.py tests/run_golden.py tests/golden/replay-envdiff.norm
git commit -m "批次4 T5：tanyin-replay 重放驱动——EV 卡片盲重放（raw_request 自解析+占位符进程内回注+scope 门链+request: 记账）+三态判定（reproduced/not-reproduced/env-diff/manual→VERIFIED/REJECTED/REPAIRED 候选）+matcher-test 离线评估+.cmd 等价入口+金样面 replay-envdiff；TDD 先红后绿 4 例"
```

---

### Task 6: 重放门 eval（localhost mock 三态全链路）

**Files:**
- Create: `tests/test_replay_gate.py`（新建；in-thread mock 目标）

**Interfaces:**
- Consumes: T3（P4 断言强制）、T5（tanyin-replay）；既有 `set-replay-state`/`ledger-replay-summary`/`tanyin-phases gate`。
- Produces: 重放门 eval（批次 4 出口验收③的判定主体）——三态全链路证明：replay→set-replay-state→replay-summary→P4 门。

- [ ] **Step 1: 写测试**（`tests/test_replay_gate.py` 全文）

```python
# -*- coding: utf-8 -*-
"""批次4 T6：重放门 eval——localhost mock 三态全链路（replay→set-replay-state→summary→P4 门）。

mock 目标（127.0.0.1 随机端口，授权内：scope include=127.0.0.1）：
  /ok      200 errorCode:00000 "total":42   → reproduced（VERIFIED 维持 C1）
  /drift   403                              → not-reproduced（REJECTED 降 C3）
  （第三个 EV 指向未监听端口）              → env-diff（REPAIRED 候选）
"""
import http.server, json, os, shutil, socketserver, subprocess, sys, tempfile, threading, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
REPLAY = os.path.join(ROOT, "cli", "tanyin-replay")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T09:30:00Z"


def call(cli, *args):
    return subprocess.run([sys.executable, cli] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/ok"):
            body = 'errorCode:00000 "total":42'
            self.send_response(200)
        else:
            body = "forbidden"
            self.send_response(403)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *a):
        pass


class TestReplayGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = socketserver.TCPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        # 授权 127.0.0.1（scope include 追加）+三张 EV 卡片
        self.call("add-scope", "--kind=include", "--matcher=127.0.0.1", "--timestamp=" + TS)
        self.evs = []
        for i, (path, m) in enumerate((("/ok", "word+status"), ("/drift", "status"), ("/gone", "word"))):
            r = self.call("add-evidence", "--title=重放%d" % i, "--source-type=command",
                          "--observed-at=" + TS, "--network-position=same-host",
                          "--repro-command=curl http://127.0.0.1:%d%s" % (self.port, path),
                          "--repro-kind=single", "--artifact=replay-art/%d.txt" % i,
                          "--timestamp=" + TS)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            ev = r.stdout.splitlines()[0].split("\t")[1]
            card = os.path.join(self.gd, "evidence", ev + ".md")
            exp = ('---\nid: %s\nnetwork_position: same-host\nraw_request: |\n'
                   "  GET %s HTTP/1.1\n  Host: 127.0.0.1\nexpected:\n"
                   "  matchers:\n    - {type: word, words: [errorCode:00000]}\n"
                   "    - {type: status, status: [200]}\npair_group: \n---\n## 摘\n" % (ev, path))
            open(card, "w", encoding="utf-8", newline="\n").write(exp)
            self.evs.append(ev)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def call(self, *args):
        return call(LEDGER, *args, "--goal-dir", self.gd)

    def replay(self, ev, port):
        return call(REPLAY, "replay", "--goal-dir", self.gd, "--id=" + ev,
                    "--scheme=http", "--port=%d" % port, "--timeout=3", "--timestamp=" + TS)

    def test_three_states_and_summary_green(self):
        v1 = json.loads(self.replay(self.evs[0], self.port).stdout.strip().splitlines()[-1])
        self.assertEqual(v1["verdict"], "reproduced")
        v2 = json.loads(self.replay(self.evs[1], self.port).stdout.strip().splitlines()[-1])
        self.assertEqual(v2["verdict"], "not-reproduced")
        v3 = json.loads(self.replay(self.evs[2], 1).stdout.strip().splitlines()[-1])
        self.assertEqual(v3["verdict"], "env-diff")
        # 三态落账（P4 子代理据此调用；本测试直接执行建议命令）
        for ev, st in ((self.evs[0], "VERIFIED"), (self.evs[1], "REJECTED"), (self.evs[2], "REPAIRED")):
            r = self.call("set-replay-state", "--id=" + ev, "--state=" + st)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.call("ledger-replay-summary")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)
        # 链一致（request:/replay-probe 事件照常入链）
        self.assertEqual(self.call("verify-chain").returncode, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑红→绿**

本任务无新实现（消费 T3/T5/既有命令）——先跑确认红点只在集成缝隙（如夹具卡片缺 Host 行报 REJECT），修补测试自身；Run: `python3 -m unittest tests.test_replay_gate -v` → 全 PASS。若暴露 T5 实现 bug，回 T5 修复后复跑（纪律：先定位再改实现，不放松断言）。

- [ ] **Step 3: 全量回归+commit**

Run: `python3 -m unittest discover -s tests` + `python3 tests/run_golden.py` → 全绿零漂移。

```bash
git add tests/test_replay_gate.py
git commit -m "批次4 T6：重放门 eval——127.0.0.1 mock 目标三态全链路（reproduced 维持/REJECTED 降级/env-diff REPAIRED 候选）→set-replay-state 三态落账→replay-summary PASS→verify-chain 入链一致；出口验收③判定主体"
```

---

### Task 7: web-blackbox 四段引擎（skill 型）

**Files:**
- Create: `engines/web-blackbox/MANIFEST.md`、`engines/web-blackbox/SKILL.md`、`engines/web-blackbox/phases/{recon,surface,test,differential}.md`、`engines/web-blackbox/patterns/{submission-ok,submission-reject}.md`
- Test: `tests/test_engine_web_blackbox.py`（新建）

**Interfaces:**
- Consumes: 统一提交 schema（契约 07）；41 命令面（子代理零写权——提交文件之外不产写路径）；差分三机械规则（契约 03 §5.1）；身份矩阵五步（契约 03 §5）。
- Produces: 引擎方法论载体（T8 差分样例对引用 differential.md 语义；T14 SKILL.md 路由表引用 `engines/web-blackbox/SKILL.md`）；A1-A8×通道×落账引擎位表（侦察侧完备性出口的文档载体）。

- [ ] **Step 1: 写失败测试**（`tests/test_engine_web_blackbox.py`）

```python
# -*- coding: utf-8 -*-
"""批次4 T7：web-blackbox 引擎结构 lint——预算/段映射/命令引用/关键语义在场。"""
import os, re, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
ENG = os.path.join(ROOT, "engines", "web-blackbox")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import registry  # noqa: E402

KNOWN = registry.all_commands() | {
    "tanyin-guard", "tanyin-canary", "tanyin-egress", "tanyin-redact",
    "tanyin-budgetctl", "tanyin-phases", "tanyin-ledger",
    "tanyin-report", "tanyin-viz", "tanyin-replay"}


def tokens(text):
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return cjk + (len(text) - cjk + 3) // 4


def read(*p):
    return open(os.path.join(ENG, *p), encoding="utf-8").read()


class TestWebBlackboxEngine(unittest.TestCase):
    def test_manifest_fields(self):
        text = read("MANIFEST.md")
        for f in ("name", "kind", "version", "适用场景", "参数", "产物路径", "超时",
                  "重试策略", "幂等键", "纪律能力声明", "工具依赖", "验签公钥"):
            self.assertIn(f, text, "MANIFEST 缺字段 " + f)
        self.assertIn("kind: skill", text)

    def test_skill_budget_and_mapping(self):
        text = read("SKILL.md")
        self.assertLess(tokens(text), 2000, "引擎 SKILL ≤2K 恒载")
        for kind in ("recon", "surface", "matrix-test", "deep-dive", "authz-diff"):
            self.assertIn(kind, text, "kind→段映射缺 " + kind)

    def test_four_segments_budget(self):
        for seg, cap in (("recon", 1500), ("surface", 1500), ("test", 1500), ("differential", 1500)):
            text = read("phases", seg + ".md")
            self.assertLess(tokens(text), cap, seg + " 段 ≤1.5K")
        self.assertIn("authz-diff", read("phases", "differential.md"), "差分段须挂 authz-diff")

    def test_differential_semantics(self):
        text = read("phases", "differential.md")
        for kw in ("pair_group", "对照组", "单变量", "两次", "errorCode", "authz-diff:",
                   "auth_context", "幂等读", "account-grant"):
            self.assertIn(kw, text, "差分段缺关键语义 " + kw)

    def test_recon_a1_a8_channels(self):
        text = read("phases", "recon.md")
        for i in range(1, 9):
            self.assertIn("A%d" % i, text, "recon 段 A1-A8 通道表缺 A%d" % i)
        for t in ("cloud-storage", "human-factor"):
            self.assertIn(t, text, "G-12 新 type 未入 recon 落账表")

    def test_patterns_exist(self):
        ok = read("patterns", "submission-ok.md")
        for f in ("intent_id", "engine", "status", "facts", "findings", "assets",
                  "edges", "creds", "operations_log", "pair_group", "expected_matcher"):
            self.assertIn(f, ok)

    def test_referenced_commands_known(self):
        for dirpath, _dirs, files in os.walk(ENG):
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                text = open(os.path.join(dirpath, fn), encoding="utf-8").read()
                for m in re.finditer(r"(?:ledger-|tanyin-)([a-z][a-z0-9-]*)", text):
                    self.assertIn(m.group(0).rstrip("-"), KNOWN | registry.all_commands(),
                                  "%s 引用未知命令: %s" % (fn, m.group(0)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_engine_web_blackbox -v` → ERROR（目录不存在）。

- [ ] **Step 3: 写引擎文件**（关键两件全文，其余同法）

`engines/web-blackbox/MANIFEST.md`：

```markdown
# web-blackbox 引擎 MANIFEST（契约 08 十二字段）

| 字段 | 值 |
|---|---|
| name | web-blackbox |
| kind | skill（LLM 子代理执行；失败=格式漂移/上下文耗尽，超时=回合预算） |
| version | 1.0.0（批次 4） |
| 适用场景 | Web 黑盒测试：侦察测绘/攻击面测绘/矩阵测试/差分举证（含身份矩阵差分 authz-diff） |
| 参数 | 六要素委派单（intent_id/目标/方法论段/预算份额/纪律约束/提交路径） |
| 产物路径 | submissions/<intent-id>/{submission.json, artifacts/, operations.log} |
| 超时 | 回合预算=intent.budget_share（token 维） |
| 重试策略 | 格式漂移→打回纠错重写一次；工具失败→重试 1 次（指数退避）后换备选路径或 blocked |
| 幂等键 | intent_id（intent done 且 submission.json 存在→重入跳过） |
| 纪律能力声明 | 不适用（skill 型；子代理纪律由总控六要素+guard 承载） |
| 工具依赖 | 无独立 tools.lock 键（命令级工具经 tanyin-guard 执行通道） |
| 验签公钥 | 不适用 |
```

`engines/web-blackbox/phases/differential.md`（段④全文）：

```markdown
# 段④ 差分举证（differential）——加载：intent.kind ∈ {matrix-test, authz-diff}

单写者铁律：你只产 submissions/<intent-id>/submission.json；一切落账由总控验收后执行。

## 差分举证四原则（所有差分测试）
1. 对照组设计：anonymous 与其他 role 请求作对照；**同端点所有角色请求共享一个 pair_group**
   （PG 号铸造：tanyin-ledger next-id E-index.tsv PG <goal-id>；提交侧填 pair_group 字段）。
2. 基线±单变量：实验组与对照组响应差异仅在单变量维度→归因成立；多变量差异=证据不足，降 confidence。
3. 同请求重复 2 次确认稳定：两次结果不同→unstable，confidence 降一级（C1→C2）。
4. errorCode 语义/内容类型验证优先于状态码（契约 03 §5.1 三条机械规则原文有效）。

## 身份矩阵差分五步（kind=authz-diff 专用；前置已由总控校验：CRED 行 active+permitted_actions 覆盖）
1. 读 intent detail 的 (endpoint, role) 对（总控已从 creds×受保护端点笛卡尔积铸候选）。
2. 逐对差分重放：该 role 会话凭据一律 {{vault:cred-N}} 占位符（guard 执行点回注）；对照=anonymous+其余 role；同 PG 归组。**仅幂等读接口**——写接口须 account-grant permitted_actions 显式覆盖+L3 审批，否则只取证不执行（R12）。
3. 落账语义（提交侧）：positive→findings[]（auth_context=CRED-<id>、exploitation_status=suspected 起步、expected_matcher 必填角色/数据标识）；负结果→facts[]（kind=authz，各角色 403 一致=回归基线）；矩阵格建议 reason 前缀 authz-diff:（主矩阵标准格；新表面走 submatrix: 前缀——差分语义由本 intent kind+pair_group 承载）。
4. 重放门联动：EV 卡片 expected.matchers 必填角色/数据标识（word=角色数据标识+status）——P4 盲重放将验证。
5. 护栏：单端点差分对数上限 24（AUTHZ_DIFF_PAIR_CAP）；会话过期→提交 status=blocked 附因（总控转 intent blocked）。

## 提交输出（findings[] 单元模板）
{"title":"…","confidence":"C2","impact":"高","exploitation_status":"suspected",
 "auth_context":"CRED-<id>","reproducible_steps":["…"],"evidence_refs":["EV-<id>"],
 "location":"…","dedup_key_proposed":"…","network_position":"intranet",
 "preconditions":["持有有效会话 {{vault:cred-N}}"],"expected_matcher":{"matchers":[…],"extractors":[…]}}
```

其余三段按同模板写（recon/surface/test 各 ≤1.5K token；recon 段含 A1-A8×通道×落账表——A1 标识层/A2 网络层/A3 服务层/A4 应用层/A5 存储与云(type=cloud-storage)/A6 代码与物料/A7 人的因素(type=human-factor)/A8 关联外推(meta=extrapolated)，每类≥3 正交通道（被动/主动/内容挖掘/历史/外推）+落账命令列（add-asset --type=…+add-fact）；test 段含先合法后恶意/破坏性 payload 只取证不执行/errorCode 语义分析；surface 段含 Swagger/Actuator/Druid 探测/前端 JS=API 说明书/认证体系还原/微服务直连>内部工具>网关主 API）；patterns/submission-ok.md=契约 07 顶层 9 字段全样例+authz 单元模板；patterns/submission-reject.md=五类失败处置对照表；SKILL.md=身份/单写者/kind→段映射表/加载预算（引擎 SKILL ≤2K、段 ≤1.5K、工具输出 0 进上下文）/失败语义五类/提交纪律四要素+占位符+pair_group。

- [ ] **Step 4: 跑绿**

Run: `python3 -m unittest tests.test_engine_web_blackbox -v` → 全 PASS（预算超限时压缩文字复测）。

- [ ] **Step 5: Commit**

```bash
git add engines/web-blackbox tests/test_engine_web_blackbox.py
git commit -m "批次4 T7：web-blackbox 四段 skill 引擎——MANIFEST（契约08 十二字段）+SKILL 路由（≤2K）+四段（recon 含 A1-A8×通道×落账引擎位表/surface/test/differential 含差分五步+三机械规则+护栏）+patterns 两件；结构 lint 测试 7 例（预算/映射/语义/命令引用⊆已知面）TDD 先红后绿"
```

---

### Task 8: 身份矩阵差分样例对 + 检出率 eval（authz_matrix 投影）

**Files:**
- Create: `cli/ledger/authz_matrix.py`、`tests/make_diff_fixture.py`、`tests/eval_authz_recall.py`
- Create: `tests/fixtures/diff-authz/`（脚本铸造后入库）、`tests/fixtures/diff-authz/ground-truth.json`
- Test: `tests/test_authz_matrix.py`（含 TestAuthzMatrix+TestDiffPair 两类，一个文件）

**Interfaces:**
- Consumes: 41 面（夹具全经命令铸造保证链自洽）；T1 十一值 type（endpoint）；T2 前缀归类（authz-diff: 行）。
- Produces（T11 消费）：
  - `authz_matrix.coverage(session) -> dict`：`{"endpoints": {<endpoint-value>: {"roles": {<role>: {"covered": bool, "finding": FD-id|"", "fact": F-id|""}}}}, "roles": [<role>…], "coverage": <已覆盖对数>/<总对数>}`——role 集合=creds 现 active 行 role 去重；端点=受保护端点（facts target 命中的 endpoint 型资产）。
  - `tests/eval_authz_recall.py`（检出率 scorer）：`python3 tests/eval_authz_recall.py --goal-dir <D> --ground-truth <gt.json>` → stdout `recall=<hit>/<planted>\nMISSING\t<gt-id>…`，exit 0/1（<基线 1.0=FAIL）。匹配规则：ground-truth 条目 `{"id","endpoint","role","marker"}` 命中=存在 finding 其 auth_context 指向同 role 的 CRED 且 evidence EV 卡片 expected.matchers.word 含 marker。

- [ ] **Step 1: 写失败测试**（`tests/test_authz_matrix.py`）

```python
# -*- coding: utf-8 -*-
"""批次4 T8：role×endpoint 覆盖投影+差分样例对语义。"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import authz_matrix, core  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402

FIXD = os.path.join(HERE, "fixtures", "diff-authz")


class TestAuthzMatrix(unittest.TestCase):
    def setUp(self):
        self.s = core.Session(FIXD)

    def test_projection_shape(self):
        cov = authz_matrix.coverage(self.s)
        self.assertIn("roles", cov)
        self.assertIn("admin", cov["roles"])
        self.assertIn("user", cov["roles"])
        self.assertTrue(cov["endpoints"], "端点非空")
        total = sum(len(e["roles"]) for e in cov["endpoints"].values())
        covd = sum(1 for e in cov["endpoints"].values()
                   for r in e["roles"].values() if r["covered"])
        self.assertEqual(cov["coverage"], "%d/%d" % (covd, total))


class TestDiffPair(unittest.TestCase):
    """差分样例对：正对（BOLA finding+PG 两 EV+authz-diff: 矩阵行）+负对（fact kind=authz）。"""

    def test_positive_pair(self):
        s = core.Session(FIXD)
        T = TABLES
        fds = [r for r in s.rows("findings.tsv")
               if r[T["findings.tsv"].index("auth_context")].startswith("CRED-")]
        self.assertTrue(fds, "正对须有 auth_context≠空的 finding")
        f0 = fds[0]
        pgs = {r[T["E-index.tsv"].index("pair_group")] for r in s.rows("E-index.tsv")
               if r[T["E-index.tsv"].index("linked_finding")] == f0[0]}
        self.assertEqual(len(pgs), 1, "正对 EV 共享单 PG")
        evs = [r for r in s.rows("E-index.tsv")
               if r[T["E-index.tsv"].index("pair_group")] in pgs]
        self.assertEqual(len(evs), 2, "实验组+对照组两 EV")

    def test_negative_fact(self):
        s = core.Session(FIXD)
        T = TABLES
        neg = [r for r in s.rows("facts.tsv") if r[T["facts.tsv"].index("kind")] == "authz"]
        self.assertTrue(neg, "负对须有 fact kind=authz（回归基线）")

    def test_matrix_authz_rows(self):
        s = core.Session(FIXD)
        T = TABLES
        rows = [r for r in s.rows("matrix.tsv") if r[T["matrix.tsv"].index("reason")].startswith("authz-diff:")]
        self.assertTrue(rows, "矩阵 authz-diff: 行在场")

    def test_chain_and_validate(self):
        import subprocess
        r = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-ledger"),
                            "validate", "--goal-dir", FIXD], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-ledger"),
                            "verify-chain", "--goal-dir", FIXD], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_authz_matrix -v` → ERROR（authz_matrix 模块与 fixtures/diff-authz 不存在）。

- [ ] **Step 3: 最小实现**

`cli/ledger/authz_matrix.py`：

```python
# -*- coding: utf-8 -*-
"""身份矩阵 role×endpoint 覆盖投影（§6.5/契约 03 §5.2——不新增表，纯投影）。"""
from .schemas import TABLES


def _cell(table, row, col):
    return row[TABLES[table].index(col)]


def coverage(session):
    s = session
    roles = sorted({_cell("creds.tsv", r, "role") for r in s.rows("creds.tsv")
                    if _cell("creds.tsv", r, "status") == "active"})
    cred_role = {r[0]: _cell("creds.tsv", r, "role") for r in s.rows("creds.tsv")}
    endpoints = sorted({_cell("assets.tsv", r, "value") for r in s.rows("assets.tsv")
                        if _cell("assets.tsv", r, "type") == "endpoint"})
    covered = {}
    for f in s.rows("findings.tsv"):
        ac = _cell("findings.tsv", f, "auth_context")
        if ac.startswith("CRED-"):
            covered.setdefault(_cell("findings.tsv", f, "affected_asset_id"), set()).add(cred_role.get(ac, ""))
    negfacts = {}
    for f in s.rows("facts.tsv"):
        if _cell("facts.tsv", f, "kind") == "authz":
            negfacts.setdefault(_cell("facts.tsv", f, "target"), True)
    ast_value = {r[0]: _cell("assets.tsv", r, "value") for r in s.rows("assets.tsv")}
    out = {"roles": roles, "endpoints": {}, "coverage": ""}
    hit = total = 0
    for ep in endpoints:
        roles_map = {}
        for role in roles:
            fd = next((f[0] for f in s.rows("findings.tsv")
                       if ast_value.get(_cell("findings.tsv", f, "affected_asset_id")) == ep
                       and _cell("findings.tsv", f, "auth_context").startswith("CRED-")
                       and cred_role.get(_cell("findings.tsv", f, "auth_context")) == role), "")
            ok = bool(fd) or ep in negfacts
            roles_map[role] = {"covered": ok, "finding": fd, "fact": "" if fd else "见负结果 fact"}
            total += 1
            hit += 1 if ok else 0
        out["endpoints"][ep] = {"roles": roles_map}
    out["coverage"] = "%d/%d" % (hit, total)
    return out
```

`tests/make_diff_fixture.py`（夹具铸造脚本——全部经 CLI 命令，链自洽；产物目录 `tests/fixtures/diff-authz/`）：

```python
# -*- coding: utf-8 -*-
"""批次4 T8：差分样例对夹具铸造（正/负对）——复制 G-g1 起步，全经 41 面命令落账。"""
import os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "..", "cli", "tanyin-ledger")
TS = "2026-09-24T10:00:00Z"
A64 = "a" * 64
STEPS = [
    # 授权基线（G-g1 已含 goal/scope；补 account-grant）
    ("add-scope", ["--kind=account-grant", "--matcher=app.intranet", "--account=admin",
                   "--permitted-actions=login;read-profile", "--timestamp=" + TS]),
    # 资产：受保护端点
    ("add-asset", ["--type=endpoint", "--value=app.intranet/admin/api/users",
                   "--meta=protected", "--timestamp=" + TS]),
    # 凭据：admin+user 两 role（session）
    ("add-cred", ["--kind=session", "--role=admin", "--username-ref=admin1",
                  "--secret-ref={{vault:cred-9}}", "--scope-asset=AST-x", "--permitted-actions=read",
                  "--timestamp=" + TS]),
    ("add-cred", ["--kind=session", "--role=user", "--username-ref=user1",
                  "--secret-ref={{vault:cred-10}}", "--scope-asset=AST-x", "--permitted-actions=read",
                  "--timestamp=" + TS]),
    # authz-diff intent（裁决 R5：直达 pending）
    ("add-intent", ["--title=authz-diff app.intranet/admin/api/users×user", "--engine=web-blackbox",
                    "--kind=authz-diff", "--origin=entity", "--cred=CRED-<新铸号>",
                    "--actions=read", "--budget-share=10k;50;0.5", "--timestamp=" + TS]),
    # 正对：BOLA finding（user 拿 admin 数据）
    ("add-finding", ["--title=admin 数据可被 user 角色读取（BOLA）", "--confidence=C2", "--impact=高",
                     "--exploitation-status=suspected", "--auth-context=CRED-<user号>",
                     "--reproducible-steps=见 EV 卡片", "--affected-asset-id=AST-<端点号>",
                     "--evidence-ids=EV-<实验组>;EV-<对照组>", "--dedup-key=<AST>+wstg-authz-bola",
                     "--scope-check=in_scope", "--description-brief=差分正对",
                     "--timestamp=" + TS]),
    # 负对：fact kind=authz（各角色 403 一致）
    ("add-fact", ["--kind=authz", "--target=app.intranet/admin/api/roles",
                  "--detail=各角色 403 一致（回归基线）", "--confidence=0.9", "--timestamp=" + TS]),
    # 矩阵：authz-diff: 行（T2 首次归类放行）
    ("matrix-set", ["--attack-surface=<基线表面>", "--vuln-class=wstg-authz", "--state=x",
                    "--reason=authz-diff: user 越权读取 admin 数据", "--intent-id=INT-<号>",
                    "--timestamp=" + TS]),
]
# 铸造流程：逐命令执行；add-evidence×2（实验组/对照组）同 --pair-group PG-g1-0007；
# 卡片按契约 06 富化（raw_request/expected 含角色数据标识 marker=errorCode:00000）；
# 收尾 matrix-freeze 前 G-g1 若未冻结须先 freeze（夹具语义=authz-diff 落主矩阵标准格）。
```

（脚本落地时：ID 占位符以命令输出逐拍解析（add-cred 回显 CRED 号→注入后续参数）；EV 卡片两张由脚本在 add-evidence 后覆写富化——raw_request 分别带 admin/user 占位符、expected.matchers 同 marker；ground-truth.json 写 5 条 planted 条目：3 正对+2 负对基线。）

- [ ] **Step 4: 跑绿**

Run: `python3 tests/make_diff_fixture.py && python3 -m unittest tests.test_authz_matrix -v` → 全 PASS。
Run: `python3 tests/eval_authz_recall.py --goal-dir tests/fixtures/diff-authz --ground-truth tests/fixtures/diff-authz/ground-truth.json` → `recall=5/5`，exit 0。

- [ ] **Step 5: 检出率 eval 负路径+commit**

`tests/eval_authz_recall.py` 实现要点：读 ground-truth json→逐条按 Produces 匹配规则比对→输出 recall=hit/planted+MISSING 清单；基线=1.0（本批夹具全检出；批次 6 LLM 在环 eval 复用此 scorer，目标靶场 ≥5 认证后漏洞）。手工自测负路径：临时删一条 finding 行的会话副本跑 scorer → exit 1（不进单测，避免夹具变异）。

```bash
git add cli/ledger/authz_matrix.py tests/make_diff_fixture.py tests/eval_authz_recall.py tests/fixtures/diff-authz tests/test_authz_matrix.py
git commit -m "批次4 T8：身份矩阵差分样例对+检出率 eval——authz_matrix.role×endpoint 覆盖投影（不新增表）+diff-authz 夹具（正对 BOLA finding+同 PG 双 EV+authz-diff: 矩阵行/负对 fact kind=authz，全经 41 面铸造链自洽）+eval_authz_recall scorer（recall=hit/planted+MISSING 清单，批次 6 接 LLM 在环）；TDD 先红后绿"
```

---

### Task 9: vuln-agent 适配器（cli 型）

**Files:**
- Create: `engines/vuln-agent/MANIFEST.md`、`engines/vuln-agent/adapter.py`
- Create: `tests/fixtures/engine/vuln-agent-out/`（canned `.vuln_agent_output` 样本）
- Test: `tests/test_engine_vuln_adapter.py`（新建）
- Test/Golden: `tests/run_golden.py`（ENGINE_CMDS 增 `engine-vuln-adapter` 面）

**Interfaces:**
- Consumes: 统一提交 schema（契约 07）；vuln_agent 产物布局（八段管道 `.vuln_agent_output/{discovered_surfaces,analyzed_surfaces,vuln_plans,vuln_findings,vuln_reviews}`）。
- Produces: `python3 engines/vuln-agent/adapter.py --intent-id INT-x --out-dir submissions/INT-x --source <代码目录> [--run]` → `<out-dir>/{submission.json, operations.log}`（status∈done/blocked；--run 缺省=归一化既有输出，测试与离线路径）。归一化表（版本→字段映射 v1）：
  - discovered/analyzed surfaces → assets[]（type=source-code 或 app；value=来源文件:行）+facts[]（kind=info/service）
  - vuln_findings `VULN-`→findings[]（confidence=C2 条件实证、exploitation_status=suspected、network_position=same-host、reproducible_steps 取 Payload 段行）
  - `NOVULN-`→facts[]（kind=info，detail=复核排除）
  - `SUSPECTED-`→findings[]（confidence=C3、exploitation_status=suspected）
  - impact：CVSS 严重性 高/中/低 直映；缺失=中
  - vuln_reviews 前缀变更（复核改名）→以**最终复核前缀**为准（嵌套复核取最深一层文件名前缀）

- [ ] **Step 1: 建夹具**（`tests/fixtures/engine/vuln-agent-out/.vuln_agent_output/`）

```
discovered_surfaces/iface-rest-user-controller.md     （# 攻击面条目：类型/分类/来源/描述/发现）
analyzed_surfaces/iface-rest-user-controller.md       （### 关键控制点：SQL 拼接 + 检查缺失）
vuln_plans/user-controller/high-risk-1.md             （# 用户查询 - SQL 注入：验证目标/疑点位置/优先级：高）
vuln_findings/VULN-iface-rest-user-controller-1.md    （**类型**：SQL 注入 **位置**：UserController.java:96
                                                        **CVSS 评分**：8.1 **严重性**：高 + Payload 段 + 事实依据段）
vuln_findings/NOVULN-iface-rest-user-controller-2.md  （复核排除：参数化 #{} 已覆盖）
vuln_findings/SUSPECTED-iface-rest-user-controller-3.md（信息不足）
vuln_reviews/VULN-VULN-iface-rest-user-controller-1.md（复核维持 VULN 前缀）
```

- [ ] **Step 2: 写失败测试**（`tests/test_engine_vuln_adapter.py`）

```python
# -*- coding: utf-8 -*-
"""批次4 T9：vuln-agent 适配器——归一化表+统一提交 schema 合规。"""
import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTER = os.path.join(HERE, "..", "engines", "vuln-agent", "adapter.py")
FIXOUT = os.path.join(HERE, "fixtures", "engine", "vuln-agent-out")


class TestVulnAdapter(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()

    def adapt(self):
        return subprocess.run([sys.executable, ADAPTER, "--intent-id", "INT-g1-0099",
                               "--out-dir", self.out, "--source", FIXOUT],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def test_submission_schema_conform(self):
        r = self.adapt()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sub = json.load(open(os.path.join(self.out, "submission.json"), encoding="utf-8"))
        for f in ("intent_id", "engine", "status", "facts", "findings", "assets",
                  "edges", "creds", "operations_log"):
            self.assertIn(f, sub)
        self.assertEqual(sub["engine"], "vuln-agent")
        self.assertEqual(sub["status"], "done")
        self.assertTrue(os.path.isfile(os.path.join(self.out, "operations.log")))

    def test_three_tier_mapping(self):
        self.adapt()
        sub = json.load(open(os.path.join(self.out, "submission.json"), encoding="utf-8"))
        by_conf = {}
        for f in sub["findings"]:
            by_conf.setdefault(f["confidence"], []).append(f)
        self.assertIn("C2", by_conf, "VULN→C2")
        self.assertIn("C3", by_conf, "SUSPECTED→C3")
        vuln = by_conf["C2"][0]
        self.assertEqual(vuln["exploitation_status"], "suspected")
        self.assertEqual(vuln["network_position"], "same-host")
        self.assertEqual(vuln["impact"], "高")
        self.assertTrue(vuln["reproducible_steps"], "Payload 段进复现步骤")
        novuln = [f for f in sub["facts"] if "排除" in f["detail"]]
        self.assertTrue(novuln, "NOVULN→fact info")

    def test_review_final_prefix_wins(self):
        self.adapt()
        sub = json.load(open(os.path.join(self.out, "submission.json"), encoding="utf-8"))
        self.assertEqual(len([f for f in sub["findings"] if f["confidence"] == "C2"]), 1,
                         "复核维持=单 VULN；复核翻案（NOVULN 前缀终态）则不进 findings")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 跑红→实现**

Run: `python3 -m unittest tests.test_engine_vuln_adapter -v` → ERROR（adapter 不存在）。实现 `engines/vuln-agent/adapter.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vuln-agent 适配器（批4 T9，契约 08 §5）——.vuln_agent_output→统一提交 schema。

--run：OS 参数化启动（POSIX python3 run.py / Windows python run.py，cwd=<source>）；
缺省=归一化既有输出（离线/测试）。归一化表=VERSION_MAP v1（版本差异容错：后续版本
新增字段在此映射，不改提交 schema）。引擎不写账本（单写者）。"""
import json, os, re, subprocess, sys, datetime

RUN_PY = {"win32": "python", "posix": "python3"}
CONF_MAP = {"VULN": "C2", "SUSPECTED": "C3"}          # NOVULN→fact(kind=info)
SEVERITY_MAP = {"高": "高", "中": "中", "低": "低"}


def parse_finding(path):
    """从 vuln_findings/*.md 提取类型/位置/CVSS/严重性/Payload（确定性正则）。"""
    text = open(path, encoding="utf-8", errors="replace").read()
    def g(p):
        m = re.search(p, text)
        return m.group(1).strip() if m else ""
    payload = re.search(r"\*\*Payload\*\*：?\n((?:    .*\n?)+)", text)
    steps = [l.strip() for l in (payload.group(1).splitlines() if payload else []) if l.strip()] \
            or ["见事实依据段（源码级路径）"]
    return {"type": g(r"\*\*类型\*\*：\s*(.+)"), "loc": g(r"\*\*位置\*\*：\s*(.+)"),
            "sev": g(r"\*\*严重性\*\*：\s*(.+)"), "steps": steps}


def final_prefix(review_dir, stem):
    """复核改名即结论变更：取最深一层复核文件名前缀（VULN/NOVULN/SUSPECTED）。"""
    cur = stem
    while True:
        cands = [f for f in os.listdir(review_dir)
                 if f.endswith(cur + ".md") and f[:-3] != cur]
        if not cands:
            return cur.split("-", 1)[0]
        cur = cands[0][:-3]


def normalize(out_root, intent_id):
    fdir, rdir = os.path.join(out_root, "vuln_findings"), os.path.join(out_root, "vuln_reviews")
    facts, findings, assets = [], [], []
    for f in sorted(os.listdir(fdir)) if os.path.isdir(fdir) else []:
        prefix, stem = f.split("-", 1)[0], f[:-3].split("-", 1)[1]
        final = final_prefix(rdir, f[:-3]) if os.path.isdir(rdir) else prefix
        if final == "NOVULN" or prefix == "NOVULN":
            facts.append({"kind": "info", "target": stem, "detail": "复核排除（NOVULN 终态）",
                          "confidence": 0.8})
            continue
        info = parse_finding(os.path.join(fdir, f))
        findings.append({
            "title": "%s %s" % (info["type"] or "疑似漏洞", info["loc"] or stem),
            "confidence": CONF_MAP.get(final, "C3"),
            "impact": SEVERITY_MAP.get(info["sev"], "中"),
            "exploitation_status": "suspected", "auth_context": "",
            "reproducible_steps": info["steps"], "evidence_refs": [],
            "location": info["loc"], "dedup_key_proposed": stem + "+src",
            "network_position": "same-host",
            "preconditions": ["目标源码可读（内部视角 L1）"],
            "expected_matcher": {}})
    sdir = os.path.join(out_root, "discovered_surfaces")
    for f in sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []:
        text = open(os.path.join(sdir, f), encoding="utf-8", errors="replace").read()
        src = re.search(r"\*\*来源\*\*：\s*(.+)", text)
        assets.append({"type": "source-code",
                       "value": (src.group(1).strip() if src else f), "meta": "surface-file=" + f})
        facts.append({"kind": "info", "target": f, "detail": "攻击面条目：" + text[:60],
                      "confidence": 0.7})
    return {"intent_id": intent_id, "engine": "vuln-agent", "status": "done",
            "facts": facts, "findings": findings, "assets": assets,
            "edges": [], "creds": [], "operations_log": "operations.log"}


def _blocked(intent_id):
    return {"intent_id": intent_id, "engine": "vuln-agent", "status": "blocked",
            "facts": [], "findings": [], "assets": [], "edges": [], "creds": [],
            "operations_log": "operations.log"}


def main(argv):
    args = dict(a.partition("=")[::2] for a in argv[1:] if a.startswith("--"))
    for k in ("--intent-id", "--out-dir", "--source"):
        if not args.get(k):
            sys.stderr.write("用法: adapter.py --intent-id=I --out-dir=D --source=S [--run]\n")
            return 2
    out_root = os.path.join(args["--source"], ".vuln_agent_output")
    os.makedirs(args["--out-dir"], exist_ok=True)
    log = open(os.path.join(args["--out-dir"], "operations.log"), "w",
               encoding="utf-8", newline="\n")
    if "--run" in argv[1:]:
        cmd = [RUN_PY.get(sys.platform, "python3"), "run.py"]
        r = subprocess.run(cmd, cwd=args["--source"], capture_output=True, text=True, timeout=3600)
        log.write("run: %s\nexit=%d\n%s\n%s\n" % (cmd, r.returncode, r.stdout, r.stderr))
        if r.returncode != 0:
            json.dump(_blocked(args["--intent-id"]),
                      open(os.path.join(args["--out-dir"], "submission.json"), "w",
                           encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
            print("OK submission.json status=blocked reason=run-exit-%d" % r.returncode)
            return 0
    if not os.path.isdir(out_root):
        log.write("env: .vuln_agent_output 缺失\n")
        sys.stderr.write("ENV: .vuln_agent_output 缺失（--run 启动或提供既有输出）\n")
        return 2
    sub = normalize(out_root, args["--intent-id"])
    json.dump(sub, open(os.path.join(args["--out-dir"], "submission.json"), "w",
                        encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1, sort_keys=True)
    log.write("normalize: findings=%d facts=%d assets=%d\n"
              % (len(sub["findings"]), len(sub["facts"]), len(sub["assets"])))
    print("OK submission.json findings=%d facts=%d assets=%d"
          % (len(sub["findings"]), len(sub["facts"]), len(sub["assets"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

`engines/vuln-agent/MANIFEST.md`：契约 08 十二字段表——name=vuln-agent；kind=cli；version=1.0.0；适用场景=源码安全分析（八段管道）；参数=`--source <代码目录> [--run]`；产物路径=`.vuln_agent_output/`→适配器归一化 submission.json+operations.log；超时=3600s；重试策略=不重试（失败显式暴露）；幂等键=intent_id；**纪律能力声明=max_op_level: read／视角上限: L1**（只读分析，无对外请求）；工具依赖=vuln-agent（tools.lock 键，批次 6 全量化登记）；验签公钥=不适用（源码包交付）。

- [ ] **Step 4: 跑绿+金样**

Run: `python3 -m unittest tests.test_engine_vuln_adapter -v` → 全 PASS。
`tests/run_golden.py` ENGINE_CMDS 增 `("engine-vuln-adapter", [sys.executable, <ADAPTER>, "--intent-id=INT-g1-0099", "--out-dir=<TMP>", "--source=<FIXOUT>"])`（norm=submission.json 规范化——剥 operations.log 时间戳）。`--bless` 建档→复跑零漂移。

- [ ] **Step 5: Commit**

```bash
git add engines/vuln-agent tests/fixtures/engine/vuln-agent-out tests/test_engine_vuln_adapter.py tests/run_golden.py tests/golden/engine-vuln-adapter.norm
git commit -m "批次4 T9：vuln-agent 适配器（cli 型）——MANIFEST（read/L1 纪律声明+OS 参数化启动 python3 run.py/python run.py）+归一化表 v1（VULN→C2/NOVULN→fact/SUSPECTED→C3+复核终态前缀优先+same-host 视角标注）+canned 夹具+金样面 engine-vuln-adapter；TDD 先红后绿 3 例"
```

---

### Task 10: nuclei adopt（模板钉 commit+sha256+ECDSA 验签，tools.lock 通道）

**Files:**
- Create: `tools.lock`、`cli/ledger/supply_chain.py`
- Create: `engines/nuclei/{MANIFEST.md, adapter.py, templates/*.yaml, templates.lock, README.md}`
- Create: `tests/fixtures/keys/`（EC 测试签名钥 TEST-ONLY）、`tests/fixtures/engine/nuclei-jsonl/`（canned 输出）
- Test: `tests/test_supply_chain.py`、`tests/test_engine_nuclei.py`

**Interfaces:**
- Consumes: 契约 10（tools.lock 每工具五字段+ECDSA 验签 6 步流程）；`tanyin-guard exec`（nuclei 经执行通道跑）。
- Produces（批次 6 tanyin-install 复用）：
  - `tools.lock` 格式：`format_version=1` 头 + 每工具一行 TSV：`<工具键>\t<版本>\t<sha256>\t<ECDSA 签名 hex>\t<模板 commit>`（非模板类末列空）。
  - `supply_chain.load_lock(path) -> dict`；`supply_chain.verify_entry(entry, pubkey_pem_path) -> (ok, reason)`（签名覆盖=行前四字段规范串的 sha256 digest；openssl 子进程验签；openssl 缺失→(False, "openssl-missing")，调用方转 ENV 语义）；`supply_chain.sign_entry(entry, privkey_pem) -> hex`（发布侧，测试/发布流程用）。
  - `engines/nuclei/adapter.py --intent-id I --out-dir D [--goal-dir G --target URL --run | --jsonl-file F]`：`--run` 先验签（tools.lock 两键+release.pub+templates.lock 逐文件 sha256）→nuclei 可执行缺失→status=blocked 提交（环境受阻，绝不自动安装）；`--jsonl-file`=canned 归一化路径（测试/离线）。JSONL→submission.json（severity→impact 映射；模板 id 进 dedup_key_proposed；matcher-name→expected_matcher word）。

- [ ] **Step 1: 建 EC 测试钥+模板快照**

```bash
mkdir -p tests/fixtures/keys engines/nuclei/templates
openssl ecparam -name prime256v1 -genkey -noout -out tests/fixtures/keys/test-signing-key.pem
openssl ec -in tests/fixtures/keys/test-signing-key.pem -pubout -out engines/nuclei/release.pub
# 两钥首行前插注记：# TEST-ONLY：批次4 验签测试钥——生产发布流程（批次 6）换真钥重签
```

模板快照三份自写 yaml（MIT/自创；上游 nuclei-templates 仅作结构范本不搬运内容）：

```yaml
# exposed-panel.yaml
id: tanyin-exposed-panel
info:
  name: Exposed Management Panel
  severity: medium
http:
  - method: GET
    path: ["{{BaseURL}}/admin"]
    matchers:
      - type: word
        words: ["管理面板", "admin dashboard"]
      - type: status
        status: [200]
```

（另两份：`actuator-leak.yaml`——/actuator/env word=properties+status 200；`swagger-leak.yaml`——/v2/api-docs word=swagger。）

`engines/nuclei/templates.lock`：首行 `upstream_commit=<40hex 固定样例>` + 每模板一行 `<相对路径>\t<sha256>`。`engines/nuclei/README.md`：快照更新流程四步（选 commit→自写/审模板→sha256 重算→重签 tools.lock）+「运行时绝不自动安装」声明。

- [ ] **Step 2: 写失败测试**（`tests/test_supply_chain.py`）

```python
# -*- coding: utf-8 -*-
"""批次4 T10：tools.lock 加载+ECDSA 验签（openssl 子进程；缺 openssl=ENV skip）。"""
import os, shutil, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
import sys
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import supply_chain  # noqa: E402

LOCK = os.path.join(ROOT, "tools.lock")
PUB = os.path.join(ROOT, "engines", "nuclei", "release.pub")
HAVE_OPENSSL = shutil.which("openssl") is not None


class TestSupplyChain(unittest.TestCase):
    def test_load_lock_entries(self):
        entries = supply_chain.load_lock(LOCK)
        for k in ("openssl", "nuclei", "nuclei-templates"):
            self.assertIn(k, entries)
        self.assertEqual(len(entries["nuclei-templates"]["commit"]), 40, "模板钉 commit 40hex")

    @unittest.skipUnless(HAVE_OPENSSL, "openssl 缺失=ENV（Windows CI 默认无；canary not-deployed 同型）")
    def test_verify_entries_and_tamper(self):
        entries = supply_chain.load_lock(LOCK)
        for k, e in entries.items():
            ok, reason = supply_chain.verify_entry(e, PUB)
            self.assertTrue(ok, "%s 验签失败: %s" % (k, reason))
        bad = dict(entries["nuclei"])
        bad["sha256"] = "0" * 64
        ok, _ = supply_chain.verify_entry(bad, PUB)
        self.assertFalse(ok, "篡改 sha256 须验签失败")

    def test_missing_openssl_reported_not_crash(self):
        """openssl 缺失=ENV 语义（非崩溃）——monkeypatch 掉 which 全平台可跑。"""
        orig = supply_chain.which
        try:
            supply_chain.which = lambda n: None
            ok, reason = supply_chain.verify_entry(
                {"key": "x", "version": "1", "sha256": "0" * 64, "sig": "00", "commit": ""}, PUB)
        finally:
            supply_chain.which = orig
        self.assertFalse(ok)
        self.assertIn("openssl-missing", reason)


if __name__ == "__main__":
    unittest.main()
``` 

- [ ] **Step 3: 跑红→实现 supply_chain+签 tools.lock**

`cli/ledger/supply_chain.py`：

```python
# -*- coding: utf-8 -*-
"""tools.lock 供应链锁定+ECDSA 验签（契约 10；批4 T10）。

签名覆盖=行前四字段规范串（键\t版本\tsha256\t）sha256 digest；验签经 openssl 子进程
（python3 stdlib 无 ECDSA——契约 10 终审先例）；fail-closed：openssl 缺失=不可判（ENV）。"""
import hashlib, os, subprocess, tempfile
from shutil import which

FIELDS = ("key", "version", "sha256", "sig", "commit")


def load_lock(path):
    entries = {}
    for ln in open(path, encoding="utf-8").read().splitlines():
        ln = ln.rstrip("\n")
        if not ln.strip() or ln.startswith("#") or ln.startswith("format_version"):
            continue
        parts = ln.split("\t")
        if len(parts) != 5:
            raise ValueError("tools.lock 行非五字段: %r" % ln)
        entries[parts[0]] = dict(zip(FIELDS, parts))
    return entries


def canonical_digest(entry):
    canon = "\t".join([entry["key"], entry["version"], entry["sha256"], ""])
    return hashlib.sha256(canon.encode("utf-8")).digest()


def verify_entry(entry, pubkey_pem):
    if which("openssl") is None:
        return False, "openssl-missing（ENV：安装 openssl 后复跑）"
    with tempfile.TemporaryDirectory() as td:
        dg, sg = os.path.join(td, "d"), os.path.join(td, "s")
        open(dg, "wb").write(canonical_digest(entry))
        open(sg, "wb").write(bytes.fromhex(entry["sig"]))
        r = subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin",
                            "-inkey", pubkey_pem, "-sigfile", sg, "-in", dg],
                           capture_output=True, text=True)
        return (r.returncode == 0), (r.stdout + r.stderr).strip()


def sign_entry(entry, privkey_pem):
    """发布侧签名（测试/发布流程用；运行时只验不签）。"""
    with tempfile.TemporaryDirectory() as td:
        dg = os.path.join(td, "d")
        open(dg, "wb").write(canonical_digest(entry))
        r = subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", privkey_pem, "-in", dg],
                           capture_output=True)
        if r.returncode != 0:
            raise RuntimeError("openssl sign 失败: " + r.stderr.decode("utf-8", "replace"))
        return r.stdout.hex()
```

签 lock（一次性步骤，产物入库；commit 占位=40 个 a 的固定样例并在 README 声明批次 6 换真 upstream commit）：

```bash
python3 - <<'EOF'
import hashlib, os, sys
sys.path.insert(0, "cli")
from ledger import supply_chain
tpl = hashlib.sha256(open("engines/nuclei/templates.lock", "rb").read()).hexdigest()
rows = [("openssl", "3.x-system", hashlib.sha256(b"system-openssl").hexdigest(), ""),
        ("nuclei", "v3.3.7", hashlib.sha256(b"nuclei-bin-placeholder").hexdigest(), ""),
        ("nuclei-templates", "snapshot-1", tpl, "a" * 40)]
key = "tests/fixtures/keys/test-signing-key.pem"
out = ["format_version=1", "# 探隐供应链锁定（批次 4 起步版；批次 6 全量化+生产钥重签）"]
for k, ver, sha, commit in rows:
    e = {"key": k, "version": ver, "sha256": sha, "sig": "", "commit": commit}
    out.append("\t".join([k, ver, sha, supply_chain.sign_entry(e, key), commit]))
open("tools.lock", "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("signed", len(rows))
EOF
```

- [ ] **Step 4: nuclei 适配器+测试+金样**

`engines/nuclei/adapter.py`（结构同 vuln-agent 适配器，差异部分）：

```python
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import supply_chain

SEV2IMPACT = {"critical": "高", "high": "高", "medium": "中", "low": "低", "info": "低"}


def verify():
    """返回 (ok, reason)；False→适配器落 blocked 提交（环境受阻语义）。"""
    lock = supply_chain.load_lock(os.path.join(ROOT, "tools.lock"))
    pub = os.path.join(HERE, "release.pub")
    for k in ("nuclei", "nuclei-templates"):
        if k not in lock:
            return False, "tools.lock 缺键 " + k
        ok, reason = supply_chain.verify_entry(lock[k], pub)
        if not ok:
            return False, "%s 验签失败: %s" % (k, reason)
    commit = lock["nuclei-templates"]["commit"]
    for ln in open(os.path.join(HERE, "templates.lock"), encoding="utf-8").read().splitlines()[1:]:
        path, _, sha = ln.rstrip("\n").rpartition("\t")
        fp = os.path.join(HERE, path)
        if not os.path.isfile(fp) or hashlib.sha256(open(fp, "rb").read()).hexdigest() != sha:
            return False, "模板快照 sha256 不符: " + path
    return True, commit


def normalize(jsonl_path, intent_id):
    findings = []
    for ln in open(jsonl_path, encoding="utf-8", errors="replace"):
        if not ln.strip():
            continue
        j = json.loads(ln)
        info = j.get("info", {})
        matcher = j.get("matcher-name") or ""
        findings.append({
            "title": info.get("name", j.get("template-id", "?")),
            "confidence": "C3",
            "impact": SEV2IMPACT.get(str(info.get("severity", "unknown")).lower(), "中"),
            "exploitation_status": "suspected", "auth_context": "",
            "reproducible_steps": ["nuclei -t %s -u %s" % (j.get("template-path", ""), j.get("host", ""))],
            "evidence_refs": [], "location": j.get("matched-at", j.get("host", "")),
            "dedup_key_proposed": j.get("template-id", "") + "+nuclei",
            "network_position": "internet",
            "preconditions": ["目标可达（internet 视角）"],
            "expected_matcher": ({"matchers": [{"type": "word", "words": [matcher]}]}
                                 if matcher else {})})
    return {"intent_id": intent_id, "engine": "nuclei", "status": "done",
            "facts": [], "findings": findings, "assets": [], "edges": [], "creds": [],
            "operations_log": "operations.log"}
```

main 流程：`verify()` 不过→blocked 提交 exit 0（log 落 reason）；`--jsonl-file`→normalize；`--run`→`shutil.which("nuclei")` 缺失→blocked（绝不自动安装）→否则 `[sys.executable, <guard>, "exec", "--goal-dir="+G, "--", "nuclei", "-jsonl", "-t", <templates>, "-u", <target>]`（stdout 落 `nuclei-output.jsonl`）→normalize。`engines/nuclei/MANIFEST.md`：kind=cli；**max_op_level=读／视角上限=L1**（黑盒工具默认最高风险级，仅 L0/L1 视角 intent 可派）；工具依赖=nuclei+nuclei-templates；验签公钥=engines/nuclei/release.pub；模板 commit 钉 tools.lock 行。

`tests/test_engine_nuclei.py` 三例：①验签不过→blocked（临时 lock 副本改 sha256→`--jsonl-file` 路径仍 blocked——验签先于归一化）；②canned 归一化（`tests/fixtures/engine/nuclei-jsonl/sample.jsonl` 两行：medium→中/high→高+matcher-name→expected_matcher）；③金样面（run_golden ENGINE_CMDS 增 `engine-nuclei-adopt`）。

- [ ] **Step 5: 跑绿+commit**

Run: `python3 -m unittest tests.test_supply_chain tests.test_engine_nuclei -v` → PASS（Windows CI openssl 例 skip=ENV）；`python3 tests/run_golden.py --bless` 后复跑零漂移；全套 discover 绿。

```bash
git add tools.lock cli/ledger/supply_chain.py engines/nuclei tests/fixtures/keys tests/fixtures/engine/nuclei-jsonl tests/test_supply_chain.py tests/test_engine_nuclei.py tests/run_golden.py tests/golden/engine-nuclei-adopt.norm
git commit -m "批次4 T10：nuclei adopt——tools.lock 起步版（openssl/nuclei/nuclei-templates 三键，契约10 五字段+format_version=1）+supply_chain 验签单源（openssl 子进程 ECDSA，fail-closed，缺 openssl=ENV）+模板离线快照（自写三模板+templates.lock 钉 commit+逐文件 sha256）+适配器（验签不过/nuclei 缺失=blocked 提交，绝不自动安装；--run 经 guard exec 执行通道）；金样面 engine-nuclei-adopt；TDD 先红后绿"
```

---

### Task 11: session-viz / tanyin-viz 投影（projector 型）

**Files:**
- Create: `engines/session-viz/MANIFEST.md`、`cli/tanyin-viz`、`cli/tanyin-viz.cmd`、`cli/ledger/viz_render.py`
- Test: `tests/test_viz.py`
- Test/Golden: `tests/run_golden.py`（ENGINE_CMDS 增 `viz-data` 面）

**Interfaces:**
- Consumes: 13 表+timeline（只读）；T8 `authz_matrix.coverage`（身份矩阵视图）。
- Produces: `tanyin-viz render --goal-dir D --out <path.html> [--data-only]` → 单文件自包含 HTML（R4：零依赖 SVG+vanilla JS）；数据岛=`<script id="tanyin-data" type="application/json">…</script>`；`viz_render.build_island(session) -> dict`（键=stats/phases/graph/rightpanel/authz_matrix；确定性=全排序输入零墙钟）；`--data-only` 输出数据岛 JSON（金样面）。零回写不变式（测试断言）。

- [ ] **Step 1: 写失败测试**（`tests/test_viz.py` 全文）

```python
# -*- coding: utf-8 -*-
"""批次4 T11：tanyin-viz 投影——数据岛/身份矩阵视图/零回写/确定性。"""
import hashlib, json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VIZ = os.path.join(HERE, "..", "cli", "tanyin-viz")
FIXD = os.path.join(HERE, "fixtures", "diff-authz")


def fingerprint(gd):
    out = []
    for dirpath, _d, files in os.walk(gd):
        for fn in sorted(files):
            p = os.path.join(dirpath, fn)
            out.append(os.path.relpath(p, gd) + ":"
                       + hashlib.sha256(open(p, "rb").read()).hexdigest()[:12])
    return sorted(out)


def render(gd, out):
    return subprocess.run([sys.executable, VIZ, "render", "--goal-dir", gd, "--out", out],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestViz(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIXD, os.path.join(self.tmp, "diff-authz"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_render_selfcontained_with_authz_view(self):
        out = os.path.join(self.tmp, "session.html")
        r = render(self.gd, out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        html = open(out, encoding="utf-8").read()
        self.assertIn('id="tanyin-data"', html)
        self.assertNotIn("http://", html.replace("http://www.w3.org", ""),
                         "零外部引用（W3C 命名空间除外）")
        island = html.split('id="tanyin-data" type="application/json">', 1)[1].split("</script>", 1)[0]
        data = json.loads(island)
        for k in ("stats", "phases", "graph", "rightpanel", "authz_matrix"):
            self.assertIn(k, data)
        self.assertTrue(data["authz_matrix"]["endpoints"], "身份矩阵视图非空（role×endpoint 投影）")
        self.assertIn("coverage", data["authz_matrix"])

    def test_zero_writeback(self):
        before = fingerprint(self.gd)
        render(self.gd, os.path.join(self.tmp, "session.html"))
        self.assertEqual(fingerprint(self.gd), before, "projector 零回写")

    def test_deterministic(self):
        digests = []
        for i in range(2):
            out = os.path.join(self.tmp, "s%d.html" % i)
            render(self.gd, out)
            digests.append(hashlib.sha256(open(out, "rb").read()).hexdigest())
        self.assertEqual(digests[0], digests[1], "两次渲染字节一致（确定性）")


if __name__ == "__main__":
    unittest.main()
``` 

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_viz -v` → ERROR（入口不存在）。

- [ ] **Step 3: 实现**（`cli/ledger/viz_render.py` 数据岛+模板）

```python
# -*- coding: utf-8 -*-
"""viz 数据岛构建+HTML 渲染（批4 T11；R4 零依赖 SVG——确定性分层布局）。

只读 13 表+timeline；数据岛全排序确定性；HTML 内联 vanilla JS（过滤/搜索/面板切换/节点详情）。"""
import json
from . import authz_matrix
from .schemas import TABLES

EDGE_STYLE = {"attack": "gold", "cross_ref": "dashed", "supersedes": "dotted",
              "scope-rel": "gray"}          # 其余六边 solid
NODE_TABLES = (("goals.tsv", "G"), ("intents.tsv", "INT"), ("assets.tsv", "AST"),
               ("facts.tsv", "F"), ("findings.tsv", "FD"), ("E-index.tsv", "EV"), ("creds.tsv", "CRED"))
LAYER = {"G": 0, "INT": 1, "AST": 2, "CRED": 2, "F": 3, "FD": 4, "EV": 5}


def build_island(s):
    counts = {t: len(s.rows(t)) for t in sorted(TABLES)}
    conf = {}
    ti = TABLES["findings.tsv"]
    for r in s.rows("findings.tsv"):
        key = "%s×%s" % (r[ti.index("confidence")], r[ti.index("impact")])
        conf[key] = conf.get(key, 0) + 1
    tle = TABLES["timeline.tsv"]
    phases = [r[tle.index("event")] for r in s.rows("timeline.tsv")
              if r[tle.index("event")].startswith("gate-exit:")]
    nodes = []
    for t, prefix in NODE_TABLES:
        for r in sorted(s.rows(t), key=lambda r: r[0]):
            cand = (t == "intents.tsv" and r[TABLES[t].index("status")] == "candidate")
            nodes.append({"id": r[0], "kind": prefix, "layer": LAYER[prefix],
                          "label": r[0], "candidate": cand})
    te = TABLES["edges.tsv"]
    edges = [{"src": r[te.index("source_id")], "dst": r[te.index("target_id")],
              "kind": r[te.index("kind")]} for r in sorted(s.rows("edges.tsv"), key=lambda r: r[0])]
    unconsumed = [r[0] for r in sorted(s.rows("facts.tsv"), key=lambda r: r[0])
                  if not any(e[te.index("kind")] == "derived_from"
                             and e[te.index("source_id")] == r[0]
                             for e in s.rows("edges.tsv"))]
    origins = {}
    for r in s.rows("intents.tsv"):
        o = r[TABLES["intents.tsv"].index("origin")]
        origins[o] = origins.get(o, 0) + 1
    cleanup_open = sum(1 for r in s.rows("timeline.tsv")
                       if r[tle.index("revert_cmd")] and not r[tle.index("event")].startswith("reverted"))
    return {"stats": {"counts": counts, "confidence": conf,
                      "matrix_rows": len(s.rows("matrix.tsv"))},
            "phases": phases,
            "graph": {"nodes": nodes, "edges": edges, "edge_style": EDGE_STYLE},
            "rightpanel": {"unconsumed_facts": unconsumed, "storm_origins": origins,
                           "cleanup_open": cleanup_open},
            "authz_matrix": authz_matrix.coverage(s)}
```

`render_html(s)`=模板插值（TEMPLATE 含：统计栏 div（counts+confidence 分色图例：C1 绿/C2 黄/C3 灰/➖🛑 红；攻击链数=attack 边计数；矩阵覆盖率=非空格/全格；收敛进度=converge 语义计数；预算进度条=budget-check 摘要列）+Pipeline 时间轴（gate-exit 序列，当前高亮=最后一门）+SVG 图谱区（分层坐标 x=200+layer*160 / y=40+col*36；attack 金色/cross_ref 虚线/supersedes 点线/candidate 半透明 node opacity=0.45；过滤按钮按 kind+搜索框+布局切换=分层/力导向两档纯计算）+右面板（节点详情/未消费 fact 清单/风暴 origin 徽章+score+via/清理清单核销状态/身份矩阵 role×endpoint 覆盖表 covered=■））。JS 四函数（svgLayered/renderStats/renderPhases/renderPanel）各 15-25 行 vanilla——落地补全于 TEMPLATE script 内，不得引外部资源。`cli/tanyin-viz` 入口（tanyin-replay 同骨架+`--data-only`）。`engines/session-viz/MANIFEST.md`：kind=projector（只读账本、产物不回写）；载体=cli/tanyin-viz；视图五区清单。`cli/tanyin-viz.cmd`=`py -3` 包装。

- [ ] **Step 4: 跑绿+金样+commit**

Run: `python3 -m unittest tests.test_viz -v` → 全 PASS；run_golden 增 `viz-data` 面（`--data-only` 对 fixtures/diff-authz）→`--bless`→零漂移。

```bash
git add engines/session-viz cli/tanyin-viz cli/tanyin-viz.cmd cli/ledger/viz_render.py tests/test_viz.py tests/run_golden.py tests/golden/viz-data.norm
git commit -m "批次4 T11：session-viz 投影（projector 型）——tanyin-viz 载体（+.cmd）数据岛五区（统计栏 confidence×impact 分色/attack 链/矩阵覆盖率/预算条；Pipeline 时间轴；图谱十边样式 attack 金/cross_ref 虚/supersedes 点/candidate 半透明+过滤搜索；右面板未消费 fact+风暴 origin+清理核销；身份矩阵 role×endpoint 投影）；零依赖 SVG（R4）+零回写+两次渲染字节一致；金样面 viz-data"
```

---

### Task 12: 侦察金丝雀 G-13（recon-deploy/recon-recall + denominator-ready ④）

**Files:**
- Modify: `cli/tanyin-canary`（增两子命令）
- Modify: `cli/ledger/phases_engine.py`（`denominator_ready` 增④断言+stats 两键）
- Modify: `phases/PROTOCOL.md`（§4 勘误补记：三断言→四断言；G-8 canary 参数语义注记一并并入）
- Modify: `phases/P2.md`（分母就绪门节补④）
- Test: `tests/test_recon_canary.py`（新建）
- Test/Golden: `tests/golden/phases-denominator-ready.norm`（**有意刷新**：stats 行增 planted/found）

**Interfaces:**
- Consumes: canary 既有 `append_tl` 律；`denominator_ready` 读侧约定（PROTOCOL §4）。
- Produces（T13 消费；evals 消费）：
  - `tanyin-canary recon-deploy --goal-dir D --value <诱饵资产值> --type <assets.type 十一值> [--note=计划编号] [--timestamp=T]` → 追加 `canary/recon-decoys.tsv` 行（`type\tvalue\tplanted_at\tnote`，无表头、只增）+timeline `recon-decoy-deploy <value> type=<t>`；重复 value=REJECT exit 1。
  - `tanyin-canary recon-recall --goal-dir D` → 比对诱饵表×assets.tsv（同 value 且 in_scope）→ stdout `recall=<found>/<planted> found=<...> missing=<...>` JSON+文本；timeline `recon-decoy-recall found=<f> planted=<p>`。
  - `denominator-ready` 第④断言：`planted>0 且 found<planted`→FAIL 清单列缺失诱饵；`planted=0 且无披露 fact（target=canary:recon 的 fact 行）`→FAIL 提示披露或部署；stats 增 `planted/found` 两键（PASS 行同步）。

- [ ] **Step 1: 写失败测试**（`tests/test_recon_canary.py`）

```python
# -*- coding: utf-8 -*-
"""批次4 T12：侦察金丝雀（G-13）——recon-deploy/recon-recall+denominator ④。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CANARY = os.path.join(ROOT, "cli", "tanyin-canary")
PHASES = os.path.join(ROOT, "cli", "tanyin-phases")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T11:00:00Z"


def run(cli, gd, *args):
    return subprocess.run([sys.executable, cli] + list(args) + ["--goal-dir", gd],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestReconCanary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_deploy_and_recall_miss_then_hit(self):
        r = run(CANARY, self.gd, "recon-deploy", "--value=decoy1.shop.example",
                "--type=subdomain", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(CANARY, self.gd, "recon-deploy", "--value=decoy1.shop.example",
                "--type=subdomain", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1, "重复诱饵=REJECT")
        r = run(CANARY, self.gd, "recon-recall")
        self.assertEqual(r.returncode, 0)
        self.assertIn("0/1", r.stdout)
        # 诱饵被发现（测绘落账）→召回满
        r = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-ledger"),
                            "add-asset", "--type=subdomain", "--value=decoy1.shop.example",
                            "--timestamp=" + TS, "--goal-dir", self.gd],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(CANARY, self.gd, "recon-recall")
        self.assertIn("1/1", r.stdout)

    def test_denominator_gate4_paths(self):
        # 路径一：未部署且未披露→FAIL
        r = run(PHASES, self.gd, "denominator-ready")
        self.assertEqual(r.returncode, 1)
        self.assertIn("④", r.stdout + r.stderr)
        # 路径二：未部署但披露 fact→④过（其余断言若挂不影响本例判断——只查④行不在 FAIL 清单）
        subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-ledger"),
                        "add-fact", "--kind=info", "--target=canary:recon",
                        "--detail=客户暂不配合植入（披露）", "--confidence=0.9",
                        "--timestamp=" + TS, "--goal-dir", self.gd],
                       capture_output=True, text=True)
        r = run(PHASES, self.gd, "denominator-ready")
        self.assertNotIn("④召回", r.stdout)
        # 路径三：部署 1 未发现→FAIL 列缺失诱饵
        run(CANARY, self.gd, "recon-deploy", "--value=decoy2.shop.example",
            "--type=subdomain", "--timestamp=" + TS)
        r = run(PHASES, self.gd, "denominator-ready")
        self.assertIn("decoy2", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_recon_canary -v` → FAIL/ERROR（子命令不存在；denominator 无④）。

- [ ] **Step 3: 最小实现**

`cli/tanyin-canary` 增（`decoys/append_tl` 复用既有函数）：

```python
def cmd_recon_deploy(gd, rest):
    kv = dict(a.partition("=")[::2] for a in rest if a.startswith("--"))
    if not kv.get("--value") or not kv.get("--type"):
        sys.stderr.write("recon-deploy 缺 --value/--type" + chr(10))
        return 2
    types = {"root-domain", "subdomain", "ip", "service", "app", "endpoint", "source-code",
             "pivot", "foothold", "cloud-storage", "human-factor"}
    if kv["--type"] not in types:
        sys.stderr.write("REJECT type 不在十一值枚举: " + kv["--type"] + chr(10))
        return 1
    d = os.path.join(gd, "canary")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "recon-decoys.tsv")
    rows = [l.split(TAB) for l in open(p, encoding="utf-8").read().splitlines()] if os.path.exists(p) else []
    if any(r[1] == kv["--value"] for r in rows):
        sys.stderr.write("REJECT 诱饵 value 重复: " + kv["--value"] + chr(10))
        return 1
    ts = kv.get("--timestamp", EPOCH)
    rows.append([kv["--type"], kv["--value"], ts, kv.get("--note", "")])
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(chr(10).join(TAB.join(r) for r in rows) + chr(10))
    append_tl(gd, ts, "P1", "recon-decoy-deploy %s type=%s" % (kv["--value"], kv["--type"]))
    print("OK recon-decoy deploy %s -> canary/recon-decoys.tsv" % kv["--value"])
    return 0


def cmd_recon_recall(gd, rest):
    p = os.path.join(gd, "canary", "recon-decoys.tsv")
    if not os.path.exists(p):
        sys.stderr.write("REJECT 无 recon-decoys.tsv（先 recon-deploy）" + chr(10))
        return 1
    decoys = [l.split(TAB)[:2] for l in open(p, encoding="utf-8").read().splitlines() if l.strip()]
    s = core.Session(gd)
    ai = TABLES["assets.tsv"].index("in_scope")
    vi = TABLES["assets.tsv"].index("value")
    have = {r[vi] for r in s.rows("assets.tsv") if r[ai] in ("in_scope", "1", "true")}
    found = [d for d in decoys if d[1] in have]
    missing = [d[1] for d in decoys if d[1] not in have]
    append_tl(gd, EPOCH, "P1", "recon-decoy-recall found=%d planted=%d" % (len(found), len(decoys)))
    print(json.dumps({"recall": "%d/%d" % (len(found), len(decoys)),
                      "found": [d[1] for d in found], "missing": missing},
                     ensure_ascii=False, sort_keys=True))
    return 0
```

（main 分发表增两子命令；usage 行同步。）

`cli/ledger/phases_engine.py` `denominator_ready` 末段增（stats 初始化同步两键）：

```python
    # ④诱饵召回率（G-13，完备性 §1.3②——planted=0 须披露，>0 须全发现）
    decoy_p = os.path.join(goal_dir, "canary", "recon-decoys.tsv")
    planted = []
    if os.path.exists(decoy_p):
        ai, vi = TABLES["assets.tsv"].index("in_scope"), TABLES["assets.tsv"].index("value")
        have = {r[vi] for r in arows if r[ai] in DENOM_IN_SCOPE_VALUES}
        planted = [l.split("\t")[1] for l in open(decoy_p, encoding="utf-8").read().splitlines()
                   if l.strip()]
        missing = [v for v in planted if v not in have]
        stats["planted"], stats["found"] = len(planted), len(planted) - len(missing)
        if missing:
            fails.append("④召回 诱饵未发现 %d/%d：%s（测绘召回率=发现/植入——完备性 §1.2 金丝雀）"
                         % (len(planted) - len(missing), len(planted), ";".join(missing[:5])))
    else:
        stats["planted"], stats["found"] = 0, 0
        disclosed = any(_cell("facts.tsv", f, "target") == "canary:recon" for f in frows)
        if not disclosed:
            fails.append("④召回 未部署侦察诱饵且未披露（tanyin-canary recon-deploy 植入，或 "
                         "add-fact --target=canary:recon --detail=不配合理由）")
```

（`cmd_denominator_ready` PASS 行格式串增 `planted=%d found=%d`。PROTOCOL §4 勘误补记：三断言→四断言全文+G-8 canary 参数语义注记（deploy/probe/recon-deploy/recon-recall 干跑口径：recon-deploy/recon-recall 本地落表与读账、零网络）。P2.md 分母就绪门节补④一行。）

- [ ] **Step 4: 跑绿+金样有意刷新**

Run: `python3 -m unittest tests.test_recon_canary tests.test_phases_gate -v` → 全 PASS。
Run: `python3 tests/run_golden.py` → `phases-denominator-ready.norm` FAIL=**有意刷新**（G-g1 无诱饵表→planted=0 found=0 且无披露 fact→输出含④——注意：若金样从 PASS 判定改为 FAIL 判定，norm 面改为对"补披露 fact 后的 G-g1 副本"生成——执行者按"补 fact 使①-④全过"的夹具副本跑面，norm=PASS 行含 planted=0 found=0）→ `python3 tests/run_golden.py --bless` 刷新→复跑零漂移（commit 注明有意刷新）。

- [ ] **Step 5: Commit**

```bash
git add cli/tanyin-canary cli/ledger/phases_engine.py phases/PROTOCOL.md phases/P2.md tests/test_recon_canary.py tests/run_golden.py tests/golden/phases-denominator-ready.norm
git commit -m "批次4 T12：G-13 侦察金丝雀——tanyin-canary recon-deploy/recon-recall（界内诱饵登记/召回率=发现/植入，recon-decoys.tsv 只增+timeline 记账）+denominator-ready 第④断言（planted>0 须全发现；planted=0 须披露 fact target=canary:recon）+PROTOCOL §4 勘误（四断言+G-8 canary 参数语义注记一并清账）+P2.md ④行；金样 phases-denominator-ready 有意刷新（planted/found 两键）；TDD 先红后绿"
```

---

### Task 13: 触发器闭包审计（TRIGGERS 目录 + trigger-audit + egress-compile 事件）

**Files:**
- Create: `phases/TRIGGERS.md`（版本化触发器目录）
- Modify: `cli/ledger/phases_engine.py`（增 `trigger_audit`+`cmd_trigger_audit`+main 分发）
- Modify: `cli/tanyin-egress`（compile 追加 timeline 事件）
- Modify: `phases/PROTOCOL.md`（§5 trigger-audit 新节——b4 追加件，同 §4 先例）
- Test: `tests/test_trigger_audit.py`（新建）

**Interfaces:**
- Consumes: 完备性设计 §3.1 触发器目录（八类）；timeline 事件词（`add-asset`/`add-cred`/`amend-scope`/`submatrix-mint`/`egress-compile`）。
- Produces: `tanyin-phases trigger-audit --goal-dir D`（只读零落账；exit 0=PASS/1=FAIL 清单/2=用法）——三检查：①**目录版本一致**（TRIGGERS.md `version:` 行在场且 timeline P0 事件 `triggers-catalog <ver>` 若已记则须同版本——P0 落账该事件由 SKILL P0 序列承载，缺记=提示非失败）；②**触发器闭包**：每个 in_scope add-asset 事件→该表面有 submatrix-mint 或子矩阵行或绑定 intent（origin=recon-event）；每个 `add-cred …(session)` 事件→存在 kind=authz-diff intent 或显式延后 fact（target=authz-diff:<CRED-id> detail=理由）；每个 `amend-scope` 事件→其后存在 `egress-compile` 事件；③**清单输出**（PASS 行 `triggers=<n> closed=<n>/<n>`）。
- `cli/tanyin-egress` `cmd_compile` 末尾追加：`append-timeline 事件 egress-compile acl=<path> lines=<n>`（actor=egress；幂等重编译=事件只记不判重）。

- [ ] **Step 1: 写失败测试**（`tests/test_trigger_audit.py`）

```python
# -*- coding: utf-8 -*-
"""批次4 T13：触发器闭包审计——三检查（目录版本/闭包/清单）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PHASES = os.path.join(ROOT, "cli", "tanyin-phases")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
EGRESS = os.path.join(ROOT, "cli", "tanyin-egress")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T11:30:00Z"


def run(cli, gd, *args):
    return subprocess.run([sys.executable, cli] + list(args) + ["--goal-dir", gd],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestTriggerAudit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_catalog_file_versioned(self):
        text = open(os.path.join(ROOT, "phases", "TRIGGERS.md"), encoding="utf-8").read()
        self.assertIn("version: triggers-v1", text)
        for ev in ("asset-added", "cred-obtained", "scope-amended"):
            self.assertIn(ev, text)

    def test_baseline_session_passes(self):
        r = run(PHASES, self.gd, "trigger-audit")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)

    def test_asset_added_without_submatrix_fails(self):
        r = run(LEDGER, self.gd, "add-asset", "--type=subdomain", "--value=newapi.shop.example",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(PHASES, self.gd, "trigger-audit")
        self.assertEqual(r.returncode, 1)
        self.assertIn("newapi.shop.example", r.stdout + r.stderr)
        # 闭环二选一：铸子矩阵行（G-2）→过
        r = run(LEDGER, self.gd, "matrix-freeze", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0)
        r = run(LEDGER, self.gd, "matrix-set", "--attack-surface=newapi.shop.example",
                "--vuln-class=wstg-authz", "--state=?", "--reason=submatrix: 闭环",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(PHASES, self.gd, "trigger-audit")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_cred_session_without_authz_candidate_fails(self):
        r = run(LEDGER, self.gd, "add-cred", "--kind=session", "--role=operator",
                "--username-ref=op9", "--secret-ref={{vault:cred-11}}",
                "--permitted-actions=read", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(PHASES, self.gd, "trigger-audit")
        self.assertEqual(r.returncode, 1)
        self.assertIn("authz-diff", r.stdout + r.stderr)

    def test_egress_compile_writes_event(self):
        r = run(EGRESS, self.gd, "compile")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        tl = open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8").read()
        self.assertIn("egress-compile", tl)
        r = run(LEDGER, self.gd, "verify-chain")
        self.assertEqual(r.returncode, 0, "事件入链须一致")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_trigger_audit -v` → ERROR/FAIL（TRIGGERS.md 与子命令不存在；egress 无事件）。

- [ ] **Step 3: 最小实现**

`phases/TRIGGERS.md`（全文——版本化封闭目录，完备性 §3.1 誊录+本批三事件消费规则）：

```markdown
# 触发器目录（版本化封闭表——trigger-audit 单源）
version: triggers-v1

| 事实类 | 触发 | 后续策略（必经评估） | 消费检查（trigger-audit） |
|---|---|---|---|
| asset-added（in_scope） | add-asset 落账 | 子矩阵行铸造（matrix-set submatrix: 新表面×词表全集）+关联外推一轮+Nday 匹配 | 该表面有 submatrix-mint 事件/子矩阵行/绑定 intent（origin=recon-event） |
| asset-added（out_of_scope） | add-asset 落账 | 记录不测（理由落账，不触发收集之外动作） | 免检（界外不入审计） |
| cred-obtained | add-cred kind=session | 身份差分候选（add-intent kind=authz-diff 直达 pending）+权限面复测 | 存在 authz-diff intent 或显式延后 fact（target=authz-diff:<CRED-id>） |
| scope-amended | amend-scope 落账 | 矩阵重映射+受影响 intent 重估+egress recompile+canary 复测 | 其后有 egress-compile 事件 |
| fact(unconsumed) | add-fact 落账 | 假设风暴五路（derived_from 强制出边或显式不消费） | converge-check 既有断言（不在本表重复） |
| finding 证实 | add-finding 落账 | 同型横向排查（同类资产全量补格） | matrix-audit 抽查既有（不在本表重复） |
| 端口/服务变更 | 复扫 diff | 指纹重测+关联 CVE 复查 | 复扫 evals（批次 6） |
| 界外资产 | add-asset out_of_scope | 记录不测 | 免检 |

> 审计规则（完备性 §3.1）：本目录覆盖全部事实类型；converge-check 的"未消费事实=0"
> 与本表 trigger-audit 互补——「该触发的是否都触发了」由本表机检。
```

`cli/ledger/phases_engine.py` 增（复用 `denominator_ready` 同区既有 helper 风格）：

```python
TRIGGERS_MD = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "phases", "TRIGGERS.md")


def trigger_audit(goal_dir):
    """触发器闭包审计（完备性 §3.1；只读零落账）。返回 (fails, stats)。"""
    s = core.Session(goal_dir)
    tle = TABLES["timeline.tsv"]
    events = [r[tle.index("event")] for r in s.rows("timeline.tsv")]
    fails, closed, total = [], 0, 0

    ai, vi = TABLES["assets.tsv"].index("in_scope"), TABLES["assets.tsv"].index("value")
    surfaces = {r[0] for r in s.rows("matrix.tsv")}
    ev_by_asset = {}
    for r in s.rows("assets.tsv"):
        if r[ai] in DENOM_IN_SCOPE_VALUES:
            ev_by_asset[r[vi]] = r[vi]
    for value in sorted(ev_by_asset):
        total += 1
        has_sub = any(value in surfaces for _ in (0,)) or any(
            e.startswith("submatrix-mint " + value) for e in events)
        bound = any(_cell("intents.tsv", it, "origin") == "recon-event"
                    and (value in _cell("intents.tsv", it, "title")
                         or value in _cell("intents.tsv", it, "detail"))
                    for it in s.rows("intents.tsv"))
        if has_sub or bound:
            closed += 1
        else:
            fails.append("①asset-added %s 无子矩阵行/铸行事件/绑定 intent（G-2 通道）" % value)

    ci, ki = TABLES["creds.tsv"].index("id"), TABLES["creds.tsv"].index("kind")
    for r in s.rows("creds.tsv"):
        if _cell("creds.tsv", r, "kind") != "session":
            continue
        total += 1
        cid = r[ci]
        has_cand = any(_cell("intents.tsv", it, "kind") == "authz-diff" for it in s.rows("intents.tsv"))
        deferred = any(_cell("facts.tsv", f, "target") == "authz-diff:" + cid
                       for f in s.rows("facts.tsv"))
        if has_cand or deferred:
            closed += 1
        else:
            fails.append("②cred-obtained %s 无 authz-diff 候选/延后 fact（批次4 起强制）" % cid)

    amends = [i for i, e in enumerate(events) if e.startswith("amend-scope")]
    for i in amends:
        total += 1
        if any(e.startswith("egress-compile") for e in events[i + 1:]):
            closed += 1
        else:
            fails.append("③scope-amended #%d 后无 egress-compile 事件（recompile+复测闭环）" % i)
    ver = ""
    if os.path.exists(TRIGGERS_MD):
        for ln in open(TRIGGERS_MD, encoding="utf-8").read().splitlines():
            if ln.startswith("version:"):
                ver = ln.split(":", 1)[1].strip()
                break
    if not ver:
        fails.append("目录版本缺失：phases/TRIGGERS.md 无 version: 行")
    return fails, {"closed": closed, "total": total, "version": ver}


def cmd_trigger_audit(goal_dir, rest):
    if rest:
        sys.stderr.write("用法: tanyin-phases trigger-audit --goal-dir D（只读，无参数）\n")
        return 2
    fails, st = trigger_audit(goal_dir)
    if fails:
        print("FAIL\ttrigger-audit\t未闭合 %d 项（触发器目录 %s）" % (len(fails), st["version"]))
        for f in fails:
            print("  " + f)
        return 1
    print("PASS\ttrigger-audit\ttriggers=%d closed=%d/%d catalog=%s"
          % (st["total"], st["closed"], st["total"], st["version"]))
    return 0
```

（main 分发增 `trigger-audit`；`cli/tanyin-egress` `cmd_compile` 末尾按 Interfaces 落事件——复用 canary `append_tl` 同律的本地实现。）

- [ ] **Step 4: 跑绿+回归适配**

Run: `python3 -m unittest tests.test_trigger_audit tests.test_egress tests.test_dryrun_p0p2 -v` → 全 PASS（干跑审计若因新事件词 `egress-compile` 需扩 TABLE_EVENTS 白名单，属测试常量适配——改 tests/test_dryrun_p0p2.py 的 TABLE_EVENTS 集合并在 commit 注明；断言语义不放松）。
Run: `python3 -m unittest discover -s tests` + `python3 tests/run_golden.py` → 全绿（egress 金样面无——compile 无金样；若有漂移按有意刷新处理并注明）。

- [ ] **Step 5: PROTOCOL §5+commit**

```bash
git add phases/TRIGGERS.md cli/ledger/phases_engine.py cli/tanyin-egress phases/PROTOCOL.md tests/test_trigger_audit.py tests/test_dryrun_p0p2.py
git commit -m "批次4 T13：触发器闭包审计——phases/TRIGGERS.md 版本化封闭目录（八类事实×策略×消费检查）+tanyin-phases trigger-audit（只读三检查：目录版本/asset-added 子矩阵或绑定 intent/cred-obtained authz 候选或延后 fact/scope-amended 后 egress-compile；G-2 通道联动验证）+egress compile 落 timeline 事件（闭环③载体）+PROTOCOL §5 新节；TDD 先红后绿 5 例"
```

---

### Task 14: 总控接线与批次收口（SKILL/P2/P3/P4/README/HANDOFF/探知项台账/出口验收）

**Files:**
- Modify: `SKILL.md`（路由表/P3 派发/P4 行）、`phases/P3.md`（cred-obtained 回边全语义+asset-added 铸行命令形态）、`phases/P4.md`（已在 T3 改；本任务补 tanyin-replay 协议引用——若 T3 已含则跳过）、`phases/P2.md`（若 T12 未覆盖④行则补）
- Modify: `cli/README.md`（批次 4 节）、`docs/HANDOFF.md`（开发流水+状态快照）
- Create: `docs/design/2026-09-24-b4-discovery-notes.md`（批 4 探知项台账 G-16..G-23）

**Interfaces:**
- Consumes: T1-T13 全部交付物。
- Produces: 总控运行时接线（SKILL 路由表指向三引擎+manifest 纪律路由+重放协议）；批 4 探知项台账（后续批次移交清单）；出口验收记录。

- [ ] **Step 1: 写失败测试**（扩 `tests/test_skill_resident.py`——新增 `TestBatch4Wiring` 类）

```python
class TestBatch4Wiring(unittest.TestCase):
    def test_route_table_lists_three_engines(self):
        text = open(SKILL, encoding="utf-8").read()
        for eng in ("web-blackbox", "vuln-agent", "nuclei"):
            self.assertIn(eng, text, "路由表缺引擎 " + eng)
        self.assertNotIn("（批次 4）", text, "批次标记应摘除（已交付）")

    def test_p3_authz_diff_backedge_full_semantics(self):
        text = open(os.path.join(PHASES, "P3.md"), encoding="utf-8").read()
        self.assertIn("kind=authz-diff", text)
        self.assertNotIn("本批登记 creds 即止", text, "批次 4 前占位语应替换")

    def test_p4_replay_protocol_references_driver(self):
        text = open(os.path.join(PHASES, "P4.md"), encoding="utf-8").read()
        self.assertIn("tanyin-replay", text)

    def test_skill_budget_still_under_2k(self):
        text = open(SKILL, encoding="utf-8").read()
        self.assertLess(estimate_tokens(text), 2000)
```

- [ ] **Step 2: 跑红→接线**

Run: `python3 -m unittest tests.test_skill_resident -v` → 新类 FAIL。修改：
- `SKILL.md`：路由表行改 `引擎方法论→engines/<引擎>/SKILL.md（web-blackbox/vuln-agent/nuclei 三引擎；派发前核 MANIFEST 纪律能力：超 max_op_level/视角上限的 intent 拒派）`；P3 ③并行派发行补 `（引擎 intent 按 MANIFEST 纪律能力路由）`；P4 行补 `重放门：fresh 子代理+tanyin-replay 三态→set-replay-state`。预算复测 <2000（当前 1321，余量充足）。
- `phases/P3.md` 回边节：`cred-obtained` 行改 `add-cred --kind=session --parent-cred <父>（真值入 vault，secret_ref 占位符）→ authz-diff 候选：受保护端点×active creds role 笛卡尔积逐对 add-intent --kind=authz-diff --origin=entity --cred <CRED-id> --actions <计划动作>（直达 pending 不打分，裁决 R5；单端点对数上限 24=AUTHZ_DIFF_PAIR_CAP）`；`asset-added` 行的"子矩阵行"补命令形态 `(matrix-set --reason=submatrix: …铸新表面×词表全集，G-2)`。
- `cli/README.md` 批次 4 节：交付清单（三引擎+tanyin-replay/tanyin-viz+tools.lock+侦察金丝雀+trigger-audit）+用法四行+测试命令。

- [ ] **Step 3: 跑绿+全量回归**

Run: `python3 -m unittest discover -s tests` → 全绿（含 test_skill_resident 全部既有断言：八节/41 索引/引用⊆已知面）；`python3 tests/run_golden.py` → 零漂移。

- [ ] **Step 4: 探知项台账+HANDOFF 记账**

`docs/design/2026-09-24-b4-discovery-notes.md`（结构同 b3 台账四节）——第二节实施期增补登记 G-16..G-23（内容=下方"探知项"节全文誊录）。`docs/HANDOFF.md`：状态快照增批次 4 行（完成度+出口验收结果）；开发流水逐任务记账（T1-T14 各一行，格式照批次 3 先例）。

- [ ] **Step 5: 出口验收（下方清单逐条实跑，结果记入 HANDOFF）+commit+push**

```bash
git add SKILL.md phases/P3.md phases/P4.md phases/P2.md cli/README.md docs/HANDOFF.md docs/design/2026-09-24-b4-discovery-notes.md tests/test_skill_resident.py
git commit -m "批次4 T14：总控接线收口——SKILL 路由表三引擎+MANIFEST 纪律路由+P4 重放协议；P3 cred-obtained 回边全语义（authz-diff 候选铸造+R5 直达 pending+对数上限）+asset-added G-2 命令形态；cli/README 批次4节；探知项台账 G-16..G-23 落盘；HANDOFF 记账+出口验收 10 条实测"
git push origin main
```

---

## 出口验收清单（批次 4 整批出口；逐条附判定命令）

> 对应 §11 批次 4 行：**引擎级夹具+差分样例对+重放门 eval+身份矩阵检出率（靶场认证后漏洞）**；不绿不放行。

| # | 验收项 | 判定命令（仓库根执行） | 通过判据 |
|---|---|---|---|
| ① | 引擎级夹具（归一化金样） | `python3 tests/run_golden.py` | 全部面 PASS（含 engine-vuln-adapter/engine-nuclei-adopt/viz-data/replay-envdiff 新面）；两次执行确定性自证 |
| ② | 差分样例对 | `python3 -m unittest tests.test_authz_matrix -v` | 全 PASS：正对（auth_context+同 PG 双 EV+authz-diff: 矩阵行）/负对（fact kind=authz）；且 `python3 cli/tanyin-ledger verify-chain --goal-dir tests/fixtures/diff-authz` 退出 0 |
| ③ | 重放门 eval（三态） | `python3 -m unittest tests.test_replay_gate -v` | 全 PASS：reproduced/not-reproduced/env-diff 三态→set-replay-state 三态落账→ledger-replay-summary PASS→verify-chain PASS |
| ④ | 身份矩阵检出率 | `python3 tests/eval_authz_recall.py --goal-dir tests/fixtures/diff-authz --ground-truth tests/fixtures/diff-authz/ground-truth.json` | `recall=5/5` 且退出码 0（基线 1.0；批次 6 LLM 在环靶场 ≥5 认证后漏洞复用此 scorer） |
| ⑤ | G-2/G-12/G-13 裁决落地 | `python3 -m unittest tests.test_submatrix_mint tests.test_assets_type_b4 tests.test_recon_canary -v` | 全 PASS（铸行四条件/十一值/④断言三路径） |
| ⑥ | 全套单测 | `python3 -m unittest discover -s tests` | 全绿（批 3 基线 322 + 本批新增全绿；零 skip 除声明 ENV 的 openssl 例） |
| ⑦ | 金样零漂移 | `python3 tests/run_golden.py && git status --short tests/golden/` | 除任务内声明的有意刷新面（phases-denominator-ready）外工作树干净 |
| ⑧ | 双平台 CI（含金样回归步） | `git push origin main` 后查 GitHub Actions | 四格矩阵（ubuntu/windows × 3.11/3.12）Unit tests+Golden regression 两步全绿；Windows openssl 例=skip（ENV 语义）不算失败 |
| ⑨ | 常驻集预算 | `python3 -m unittest tests.test_skill_resident -v` | SKILL.md <2000 token（含批次 4 接线后新增文字）；八节/41 索引/引用⊆已知面全过 |
| ⑩ | 探知项台账+HANDOFF | `test -f docs/design/2026-09-24-b4-discovery-notes.md && grep -c 'G-1[6-9]\|G-2[0-3]' docs/design/2026-09-24-b4-discovery-notes.md` | 文件在场且 ≥8 条登记；HANDOFF 开发流水 T1-T14 记账齐 |

**补充判定（侦察侧完备性出口，并入⑥）**：`python3 -m unittest tests.test_trigger_audit tests.test_engine_web_blackbox -v` → 触发器闭包三检查+A1-A8 通道表+多源法定（denominator ①既有）全 PASS。

## 探知项（新接口缺口——批 4 起草期发现，登记 G-16..G-23）

| # | 缺口 | 影响 | 本批处置 | 建议裁决 |
|---|---|---|---|---|
| G-16 | **EV 卡片↔E-index 同值性的 validate 集成缺位**：设计 §4.11"卡片与 TSV 不一致=P4 ledger-validate 失败"，但 validate 只读 13 表不读卡片文件 | 同值性执法点与设计文字漂移 | tanyin-replay 在重放前校验（T4 `check_consistency`）；validate 集成不动 | 契约 v3 裁决：validate 增 `--with-cards` 可选扫卡片（需遍历交战区 card_path）或维持 replay 侧单点 |
| G-17 | **matcher 子集无精确冻结**：契约 06"以 nuclei matcher 为范本"未定子集与组合语义 | 重放判定不可金样化 | R1 裁决落地（word/status/regex+AND+fail-closed），契约 06 微版本勘误 | 已随 T4 勘误；nuclei DSL 全集支持留引擎版本演进 |
| G-18 | **nday-verify 段映射缺位**：§6.3 kind→段映射表（v2 勘误新增 kind 后）未列 nday-verify | nuclei 引擎 intent 的方法论加载路径不明 | cli 型引擎无段文件（MANIFEST 即方法论入口），契约 07 映射表补注 | 契约 07 微版本注记：nday-verify→引擎=nuclei（cli 型，无 web-blackbox 段映射） |
| G-19 | **submission 无视角/引擎全局字段**：vuln-agent 需标注视角层级（L1 内部），schema 顶层无 perspective | 视角标注只能落在 findings[].network_position=same-host | T9 以 network_position 承载（够用） | 契约 v3 裁决是否增顶层 `perspective` 字段（涉及 147 字段口径外的提交 schema） |
| G-20 | **差分对数上限常量缺源**：§6.6"单端点差分对数上限"参数无契约依据 | 护栏参数漂移 | R6：模块常量 AUTHZ_DIFF_PAIR_CAP=24+--cap 覆盖 | 契约 v3 增常量（G-3 restart_rate_minutes 同通道） |
| G-21 | **session-viz 渲染库选型**：设计载 Cytoscape.js，vendor ~370KB 大文件与金样确定性/无网络安装相抵 | 渲染能力 vs 工程纪律 | R4：v1 零依赖 SVG+vanilla JS（视图五区硬语义全保留） | 批次 6 安装矩阵期裁决：接受 vendor 大文件（tools.lock 锁 sha256）或维持零依赖 |
| G-22 | **tools.lock 生产签名密钥与发布流程缺位**：本批测试钥进仓（TEST-ONLY） | 验签链信任根未建立 | 测试钥签名三键（快照锚定有效）；生产钥=批次 6 安装器出口 | 批次 6：生产 EC 钥生成/保管/重签流程+release.pub 替换 |
| G-23 | **set-replay-state 墙钟继承**（关联批 3 Minor-5）：check_cmds \`_now()\` 墙钟进账本，重放门转强制后该通道使用频率上升 | 时间戳非确定性（金样/审计弱化） | 本批零触碰（面变更需版本化） | 提前至契约 v3：set-replay-state 增 --timestamp 通道（checkpoint 先例） |

## 与批次 3 交付物的接点（执行者须知）

| 批 3 交付物 | 批 4 接点 |
|---|---|
| phases/PROTOCOL.md（协议合订本） | T1/T3/T12/T13 四处**追加节/勘误**——§1-3 冻结文本不动（T3 的 SKIP 行退役注记为行内注记非改写） |
| tanyin-phases gate/denominator-ready | T3 改 P4 expect 触发 gate 行为；T12 扩 denominator ④——均为追加断言不动既有①②③ |
| state.md/resume-kit/kill9 体系 | 零触碰（引擎层不新增账本写路径；replay 事件走 timeline 链式续写同律） |
| G 台账（b3-discovery-notes） | G-2/G-12/G-13 终态改"已闭环·批次 4"（T14 在 b3 台账状态归并表就地更新——追加注记不改历史行） |
| run_golden --bless 门槛 | 新金样面一律 --bless 显式建档；有意刷新面在 commit+HANDOFF 双注明 |
| test_skill_resident 引用⊆已知面 | 新引擎 md 的命令引用 lint 进 test_engine_web_blackbox（同正则）；SKILL 接线后复跑既有断言 |

## Self-Review（计划起草者自查记录）

1. **规格覆盖**：§11 批次 4 行七件——web-blackbox 四段（T7）/vuln-agent 适配器（T9）/nuclei adopt 验签（T10）/session-viz（T11）/身份矩阵差分（T7 differential+T8 样例对+R5）/重放门三态（T3+T5+T6）/assets.type 扩展（T1）；出口四件——引擎级夹具（①）/差分样例对（②）/重放门 eval（③）/检出率（④）。完备性设计——A1-A8 引擎位（T7 recon 段）/多源法定（批 3 既有①，T8 夹具含双源 fact）/金丝雀（T12）/触发器闭包（T13）/分母就绪门②补全（T12）。G-2/G-12/G-13=前置裁决节+T1/T2/T12。批次 3 接点表齐。无遗漏。
2. **占位符扫描**：全文无 TBD/TODO/"适当处理"；所有代码步给全文或逐段骨架+落地注记（viz TEMPLATE 的四 JS 函数给了坐标/样式/交互规格与行数约束——属实现自由度声明而非缺内容）；执行者零上下文可开工。
3. **类型一致**：matcher 子集/R1 三态词表（reproduced/not-reproduced/env-diff/manual ↔ VERIFIED/REJECTED/REPAIRED/人工）在 T4/T5/T6/P4.md 四处一致；`authz_matrix.coverage` 返回形状 T8 定义 T11 消费一致；`supply_chain.verify_entry` 签名 T10 内两处一致；十一值枚举 T1 定义、T7 recon 段/T12 recon-deploy 三处引用一致。
