# 批次 3：总控 SKILL 路由器 + phases.yaml 引擎 + P3 演进循环 + 受管重启 + state.md/resume-kit + 幂等续跑 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付探隐总控三件套——SKILL.md 路由器（常驻权威集 <2K token）、phases.yaml 数据状态机的 CLI 侧确定性引擎（校验器+门断言执行器）、受管重启/恢复体系（state.md v2 + resume-kit 白名单 + 工件即缓存幂等续跑）。出口=干跑 P0-P2 零对外请求 + kill -9 保真度 eval 通过 + 常驻集 <2K token。

**Architecture:** 认知（SKILL.md 路由器 + phases/*.md 方法论）与确定性（cli/tanyin-phases 引擎 + 既有 41 条账本命令）分离：phases.yaml 是声明层，执法权威仍在账本命令——引擎把每门 exit 断言翻译成对既有命令的调用与返回值判定，判定协议在 phases/PROTOCOL.md 冻结（批次 3 两份批次间接口之一；另一份=常驻集清单，同文件承载）。state.md v2 行结构是 02a 终审补全 5 明文授权批次 3 冻结的接口：升级后的 checkpoint 命令原子写入，state-rebuild 对账，tanyin-phases rebuild-state 对账重建。

**Tech Stack:** python3 ≥3.9 标准库（零第三方依赖——stdlib 无 yaml，phases.yaml 用自写受限子集解析器）；unittest + 黄金夹具；Markdown 数据文件（SKILL.md / phases/*.md / phases.yaml）。

**Spec:** docs/design/2026-09-21-tanyin-v2-design.md（§5 流程/九门/受管重启护栏、§2.4 铁律 7、§5.4 生长通路、§11 批次 3 行）；contracts/04-phases.md（phases.yaml 契约）、contracts/02-commands.md + 02a（41 命令签名终审冻结）、contracts/09（CLI 工具面）、contracts/12（安装布局）。冲突时契约赢；契约未载→按本计划「探知项」节登记上报，不发明。

## Global Constraints（每个任务隐含继承）

- python3 ≥3.9 标准库，零第三方依赖；禁 pip install（ADR-P4②）。
- 一切写盘 `encoding="utf-8", newline="\n"` 恒 LF；`.gitattributes` 已钉 *.yaml/*.md/*.py/*.tsv LF（Windows checkout 不译 CRLF——链式哈希与金样字节依赖此红线）。
- Windows 等价入口：每个新入口配 `tanyin-*.cmd`（内容即 `py -3` 调用，参考既有 cli/tanyin-guard.cmd）；入口启动即 `ensure_utf8_stdio()`。
- 退出码 0=通过 / 1=门禁失败（REJECT，账本零字节变更）/ 2=用法或环境（对齐 Strix；§9.2）。
- **41 命令面冻结**：不改既有命令的名称/输出 schema/拒收语义。唯一例外=checkpoint（02a 终审补全 5 明文授权批次 3 冻结 state.md 行结构；参数追加走批次 1 探知注记 1 同型先例：必填 --timestamp 就是这么加的）。state-rebuild 输出保持 `PASS\trevision=<n>` 首行不变（金样 read-state-rebuild.norm 不回红）。
- 铁律 7（§2.4）：cli/ 只许四类能力；禁止进 CLI：攻击决策/假设生成/漏洞语义判定/「是否漏洞/下一步测什么」的判断。tanyin-phases 归「确定性账本运算」类（输入输出可字节级回归——引擎测试全部金样化）。
- 测试范式（沿用批次 1/2）：unittest；`shutil.copytree(tests/fixtures/G-g1, 临时目录)` 起底，绝不改 fixtures/；进程级用例用 `[sys.executable, 入口绝对路径, ...]`（见 tests/run_golden.py:run_cli）；拒收后断言 13 表字节不变（snapshot/unchanged helper 见 tests/test_write_cmds.py:14-38）。
- 每任务出口=该任务测试全绿 + 既有 181 单测与黄金回归（`python3 tests/run_golden.py`）不回红才 commit；commit 粒度=任务。
- CI 双平台（.github/workflows/ci.yml：ubuntu+windows × py3.11/3.12，PYTHONUTF8=1）：新测试不得只在一平台绿；平台门控用 `unittest.skipIf(os.name != "posix", ...)`。
- 时间戳确定性：一切新写命令/引擎落账时间戳取自必填 `--timestamp=<ISO8601>`（批次 1 口径），禁 datetime.now() 进账本（evals/金样可重放）。

---

## 文件结构图（每文件一个职责）

```
(仓库根 = 安装树，契约 12；★=本批新增 ◆=本批修改)

SKILL.md                        ★ 总控路由器本体：常驻权威集（<2K token）——铁律摘要/九门骨架/
                                   P3 循环/命令索引/恢复协议/受管重启触发/干跑口径/路由表。
                                   认知按需加载：九门方法论与引擎知识不进常驻，按门加载 phases/*.md。
phases/
  phases.yaml                   ★ 九门状态机数据（契约 04 定稿语义全量誊录：8 常量/9 门/21 条 exit
                                   断言/P3 三事件/3 回边）。声明层——执法权威在账本命令。
  PROTOCOL.md                   ★ 批次 3 冻结接口合订本：①断言→命令调用协议（判定表/事件词汇/
                                   幂等规则）②常驻集清单（SKILL.md 分节预算与内容边界）③干跑口径。
  P0.md P1.md P2.md P3.md       ★ 九门方法论指令（按需加载，结构头固定：duty 命令序列/entry 检查
  P4.md P5.md P5.5.md             单/exit 断言/回边）。P3.md 最厚：风暴五路/三资产事件/收敛判定/
  P6.0.md P6.md                  受管重启触发条件。人读指令——LLM 照做，命令引用一律走执行通道。
cli/
  tanyin-phases                 ★ 引擎 CLI 入口（python3 stdlib）：validate / gate / restart /
                                   resume-kit / cached / rebuild-state 六个子命令派发。
  tanyin-phases.cmd             ★ Windows py -3 等价包装。
  ledger/
    phases_engine.py            ★ 引擎库：受限 YAML 子集解析器、phases.yaml schema 校验、gate
                                   断言执行器（断言→命令调用协议实现）、managed-restart 护栏链、
                                   resume-kit 生成器、幂等 cached 判定、rebuild-state。
    state_md.py                 ★ state.md v2 冻结格式库：固定键序/解析/原子写（tmp+os.replace）/
                                   200 行硬顶。write_cmds 与 phases_engine 共用，单一实现。
    write_cmds.py               ◆ checkpoint 升级：写 state.md v2 全字段（固定 10 键+handoff 段）；
                                   启用单活跃会话锁（--session/--release/--round/--note）。
    check_cmds.py               ◆ state-rebuild 升级：v2 结构对账（revision==timeline 行数 + snapshot
                                   与账本重算一致 + 枚举合法 + 行数≤200）。输出首行格式不变。
    registry.py                 ◆ 增 all_commands()：枚举 41 基名（引擎「九门断言命令存在性」检查
                                   的单源；防双份清单漂移）。
tests/
  test_phases_yaml.py           ★ T1/T2：解析器+schema 校验器（含篡改负例）。
  test_phases_gate.py           ★ T3：gate runner（already-passed 幂等/断言真跑/gate-fail/跳门拒收）。
  test_state_md.py              ★ T4/T5：state.md v2 写读/200 行硬顶/单会话锁/原子性/state-rebuild
                                   对账/rebuild-state。
  test_managed_restart.py       ★ T6：护栏四件套（速率上限/计入预算/单会话/timeline 事件）。
  test_resume_kit.py            ★ T7：白名单内容/先对账/幂等字节一致。
  test_idempotent_resume.py     ★ T8：done+submission.json→SKIP；缺件→RUN。
  test_skill_resident.py        ★ T9/T10：常驻集 <2K token 估算/SKILL 结构 lint/命令索引一致性
                                   （SKILL.md+phases/*.md 引用命令 ⊆ 已知命令面）/九门 md 齐备。
  test_dryrun_p0p2.py           ★ T11：干跑 eval——脚本化 P0-P2 全序列，断言 timeline 零 request:
                                   与 request-ticket 事件、gate-exit:P0/P1/P2 齐备、verify-chain PASS。
  test_kill9_fidelity.py        ★ T12：kill -9 保真度 eval——确定性撕裂三态恢复 + POSIX 随机
                                   SIGKILL（seed 固定）恢复后 state-rebuild PASS。
tests/golden/
  write-checkpoint.state        ◆ 有意刷新（state.md v2 结构；旧三行格式作废——02a 终审补全 5）。
  phases-validate.norm          ★ 新增：tanyin-phases validate 输出基线。
  phases-gate-p0.norm           ★ 新增：gate P0 已过态（already-passed）输出基线。
  phases-resume-kit.norm        ★ 新增：fixture 上的 resume-kit.md 内容基线。
```

依赖顺序：T1→T2→T3（引擎竖切）；T4→T5→T6（state 竖切）；T7、T8 依赖 T1（引擎库已立）；T9、T10 相互独立可并行；T11 依赖 T3+T4+T7+T8；T12 依赖 T5+T6+T7；T13 收口最后。

---

## 批次 3 冻结接口（先读：后面所有任务以此为据）

批次 0 定死的批次间接口里，批次 3 负责交付两份：**「phases.yaml 断言→命令调用协议」与「常驻集清单」**。两份合订于 phases/PROTOCOL.md（全文如下，T3 任务把它落盘为文件；此后 Engine 与 SKILL 任何一方改动都要回来 bump 该文件头部 version）。

~~~markdown
---
version: b3-frozen-1   # 批次 3 冻结接口合订本（契约 04 §5/§11 批次 3 行）
---

# 1 断言→命令调用协议（phases.yaml exit.assert → 命令调用与返回值判定）

执法权威不搬家（设计 §5.1）：yaml 只声明「调哪条命令、期望什么返回」，判定由命令执行。
tanyin-phases gate --goal-dir D --phase <门> 是该协议的唯一确定性执行体：

1. 调用形态：exit.assert[].cmd 经 shlex 切词；首词即命令名（含 ledger- 前缀，registry 双前缀注册均可查）；剩余词做空格式旗标归一——`--k v`（v 不以 -- 开头）合并为 `--k=v`，裸旗标（如 --all-assets / --baseline / --verify-signoff）原样传递。归一后经 ledger.registry.lookup 在进程内派发（与宿主 shell 直通 tanyin-ledger <cmd> 等价；沙箱化只换通道实现，本协议不变——设计 §3.2 咬合点 1）。
2. 判定表（exit code + stdout/stderr）：

| 断言命令（cmd 首词） | 满足（PASS）判定 |
|---|---|
| 默认（ledger-validate / ledger-verify-chain / ledger-scope-coverage / ledger-tree-check / ledger-replay-summary / ledger-terminal-gate / ledger-hash-recheck / ledger-matrix-audit / ledger-redact-scan / ledger-approve --verify-signoff / ledger-approve --knowledge / tanyin-redact --reverse-verify 等） | 进程退出码 == 0 |
| ledger-converge-check | 退出码==0 且 stdout 首词 ∈ {converged, budget-exhausted}；budget-exhausted 时门事件附 `mode=degraded`（设计 §5.2 back_edges） |
| ledger-matrix-gaps --baseline | 退出码==0 且 stdout 含 `covered=true` 且 `#baseline_rows=<N>` 的 N>0（该命令 covered=false 也退出 0，必须查 stdout——批次 1 实现事实） |
| ledger-matrix-freeze | 退出码==0（新鲜冻结）；或 退出码==1 且 stderr 含 already-frozen 且 timeline 已有 matrix-freeze 事件（halt 修复后重评的幂等容忍） |
| expect 文本含「批次 4 前=SKIP」 | 记 skipped，不计失败；门事件附 `skip=<n>`（P4 重放门批次 4 转强制，SKILL/P4.md 负责报告披露） |
| tanyin-report --lint（P5） | 退出码==2 = 工具未交付（批次 6）→ 门结果=ENV-HALT（引擎退出码 2，可重跑，非门禁失败） |

3. 事件词汇（timeline，链式哈希照常）：
   - 门全过：`gate-exit:<门> asserts=<n> result=PASS[ skip=<n>][ mode=degraded]`（actor=总控，phase=<门>）——与批次 1 夹具/verify-chain 跳门检测既有格式逐字兼容（cli/ledger/core.py:GATE_EXIT_EVENT）。
   - 任一断言不满足：`gate-fail:<门> assert=<cmd 首词> reason=<一句>`（非 gate-exit 前缀——跳门检测只认 gate-exit，失败不得被误计为过门）；引擎退出码 1，语义=halt（人工处置后重评）。
4. 幂等与前置：
   - gate-exit:<门> 已存在 → 输出 `OK\tgate:<门> already-passed`，退出 0，不重复落事件。
   - 前置门检查：目标门之前的每一门都必须已有 gate-exit 事件，缺 → REJECT（退出 1，零落账）。
   - 断言命令都是既有 41 面命令：引擎不新增账本写路径；写类断言（matrix-freeze）经自身 handler 落账，链一致性由各命令自己保证。
5. entry 断言（如 P0 的「state-rebuild PASS」）：声明层人读检查单，由 SKILL/恢复协议执行；引擎只执行 exit 断言（契约 04 分工语义）。

# 2 常驻集清单（SKILL.md 预算与内容边界）

常驻权威集 = SKILL.md 全文，token 预算 <2000（设计 §11 批次 3 出口）。确定性估算口径（测试冻结）：`tokens ≈ CJK 字符数 + ⌈非 CJK 字符数 / 4⌉`（跨 tokenizer 近似；预算留 ≥100 token 余量吸收偏差——探知项 G-11）。
必含八节（缺一=结构 lint FAIL）：①身份与铁律 ②九门循环骨架 ③P3 演进循环 ④命令索引（41 名+入口路径，签名不展开）⑤恢复协议（先对账再干活）⑥受管重启触发 ⑦干跑模式口径 ⑧路由表（当前门→phases/<门>.md 按需加载）。
禁入常驻：九门方法论展开（phases/*.md）、引擎知识、知识库内容、任何账本全量数据。

# 3 干跑口径（T11 的判定依据，随本接口一并冻结）

干跑（无目标自检）= P0-P2 照常经账本命令落账，零对外请求：不调 tanyin-guard exec、不调 tanyin-canary probe；tanyin-egress 只 compile（本地产物，无网络）；canary 只 deploy（本地登记）。
判定=timeline 无 `request:` 前缀事件且无 `request-ticket` 事件，verify-chain PASS。
~~~

---
## Task 1: phases/phases.yaml 数据文件 + 受限 YAML 子集解析器

**Files:**
- Create: `phases/phases.yaml`（契约 04 定稿语义全量誊录）
- Create: `cli/ledger/phases_engine.py`（本任务只做 parse_yaml + load_phases）
- Test: `tests/test_phases_yaml.py`

**Interfaces:**
- Consumes: 契约 04（九门/常量/断言/回边的冻结语义）；`cli/ledger/core.py` 的 GATE_ORDER。
- Produces: `phases_engine.parse_yaml(text) -> dict`（受限子集；语法外输入 raise `PhasesSyntaxError`）；`phases_engine.load_phases(path=None) -> dict`（默认路径 `<repo>/phases/phases.yaml`，读文件+解析；文件缺失 raise `PhasesSyntaxError`）。Task 2 的 `validate_phases(data, known_cmds)`、Task 3 的 `run_gate` 都消费 load_phases 的返回 dict。

背景：python3 stdlib 没有 yaml 模块，而契约 04 冻结的载体是 yaml——写一个只支持契约 04 所需语法的受限解析器（fail-closed：语法外输入报错，绝不猜）。支持：块映射、块列表（`- ` 项）、行内流映射 `{k: v, ...}`、行内流列表 `[a, b, ...]`、引号/裸标量、`#` 注释（引号内不剥）、`>-` 折叠块标量（duty 长文本）。

- [ ] **Step 1: 写失败测试**（新建 `tests/test_phases_yaml.py`）

```python
# -*- coding: utf-8 -*-
"""批次 3 T1/T2：phases.yaml 解析器与 schema 校验器测试。
范式：读仓库真实 phases/phases.yaml；篡改例写临时文件，不动本体。"""
import os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr
import io

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import phases_engine as pe

YAML_PATH = os.path.join(ROOT, "phases", "phases.yaml")
GATES9 = ("P0", "P1", "P2", "P3", "P4", "P5", "P5.5", "P6.0", "P6")


class TestParse(unittest.TestCase):
    def test_loads_repo_yaml(self):
        data = pe.load_phases(YAML_PATH)
        self.assertEqual(str(data["format_version"]), "2")
        self.assertEqual(data["initial"], "P0")
        self.assertEqual([str(s) for s in data["states"]], list(GATES9))
        self.assertEqual(len(data["back_edges"]), 3)

    def test_constants_block(self):
        c = pe.load_phases(YAML_PATH)["constants"]
        self.assertEqual(len(c), 8)
        self.assertEqual(str(c["restart_context_threshold"]), "0.75")
        self.assertEqual(str(c["single_active_session"]), "true")

    def test_gate_asserts_shape(self):
        g = pe.load_phapes(YAML_PATH)["gates"] if False else pe.load_phases(YAML_PATH)["gates"]
        self.assertEqual(set(g), set(GATES9))
        a0 = g["P0"]["exit"]["assert"]
        self.assertEqual(a0[0]["cmd"], "ledger-validate --tables goals,scope,creds")
        self.assertEqual(str(a0[0]["expect"]), "PASS")
        self.assertEqual(len(g["P4"]["exit"]["assert"]), 5)   # 21 条断言分布 P0=3/P1=3/P2=2/P3=1/P4=5/P5=3/P5.5=1/P6.0=1/P6=2
        ev = g["P3"]["events"]
        self.assertEqual(set(ev), {"asset-added", "cred-obtained", "scope-amended"})

    def test_folded_duty_is_string(self):
        duty = pe.load_phases(YAML_PATH)["gates"]["P0"]["duty"]
        self.assertIsInstance(duty, str) and self.assertIn("ledger-add-goal", duty)

    def test_syntax_error_fail_closed(self):
        with self.assertRaises(pe.PhasesSyntaxError):
            pe.parse_yaml("a: [unclosed")
        with self.assertRaises(pe.PhasesSyntaxError):
            pe.parse_yaml("no colon line")

    def test_comment_and_quote(self):
        d = pe.parse_yaml("k: \"v # not comment\"  # real comment\nj: [a, b]")
        self.assertEqual(d["k"], "v # not comment")
        self.assertEqual(d["j"], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_phases_yaml -v`
Expected: FAIL/ERROR（ModuleNotFoundError: ledger.phases_engine / phases.yaml 不存在）

- [ ] **Step 3: 落盘 phases/phases.yaml（契约 04 全量誊录，duty 用 >- 折叠）**

```yaml
# 探隐 TanYin · phases.yaml（九门状态机·声明层）
# 契约：contracts/04-phases.md（schema_version=2）＋设计定稿 §5.2。
# 执法权威在账本命令：每条 exit 断言=命令调用与返回值判定（phases/PROTOCOL.md）。
format_version: 2
constants:
  restart_context_threshold: 0.75
  restart_every_n_rounds: 10
  storm_score_threshold_base: 0.5
  llm_association_quota: 5
  reversal_scan_quota: 3
  p4_sample_ratio: 0.2
  single_active_session: true
  budget_dollars_enabled: false
states: [P0, P1, P2, P3, P4, P5, P5.5, P6.0, P6]
initial: P0
gates:
  P0:
    title: 授权门
    entry: {assert: ["交战区目录可用", "无既有 goal 或处于 resume 态（state-rebuild PASS）"]}
    duty: >-
      八问问卷+业务问卷（§8.1）→ ledger-add-goal → scope/creds 落账（含 oob/account-grant/amendment 语义）
      → 授权书扫描件入 evidence（双哈希）→ SKILL 版本+tools.lock 哈希落 timeline → egress compile → canary 部署
    exit:
      assert:
        - {cmd: "ledger-validate --tables goals,scope,creds", expect: PASS}
        - {cmd: "ledger-scope-coverage", expect: "include+exclude+oob 齐备"}
        - {cmd: "ledger-verify-chain", expect: PASS}
      on_pass: P1
      on_fail: halt
  P1:
    title: 测绘
    entry: {require: "P0.exit"}
    duty: >-
      侦察子代理（六要素委派）→ assets/facts 落账（每资产 scope-check 内联；facts 即脱敏）；
      测绘不终于 P1——P3 全程可经 asset-added 事件续测（§5.4 生长通路①）
    exit:
      assert:
        - {cmd: "ledger-tree-check --complete parent", expect: PASS}
        - {cmd: "ledger-scope-check --all-assets", expect: "全部资产已判定"}
        - {cmd: "ledger-validate", expect: PASS}
      on_pass: P2
  P2:
    title: 规划
    duty: >-
      读账本+知识库指纹匹配（先例三元组内）→ matrix-init（列从 VOCAB WSTG v4.2 钉死）→ 冻结
      （锚点冻结≠探索冻结——分母不动，新资产走子矩阵，§4.10/§5.4）
    exit:
      assert:
        - {cmd: "ledger-matrix-freeze", expect: "frozen（不可重复冻结）"}
        - {cmd: "ledger-matrix-gaps --baseline", expect: "基线行数>0 且覆盖全部 in_scope 攻击面"}
      on_pass: P3
  P3:
    title: 演进循环
    duty: >-
      每轮：⓪checkpoint+budget-check → ①扫描（unconsumed-facts/pending-intents/matrix-gaps）
      → ②条件触发假设风暴（五路+dedup+阈值递增）→ ③批量并行派发（指挥官协议，六要素+预算份额）
      → ④验收落账（单写者，写前拒收）→ ⑤链构建（attack/cross_ref）→ ⑥收敛判定
    events:
      asset-added: {action: "spawn 测绘 intents（origin=recon-event，直接 pending，不打分）+子矩阵初始化", guardrails: "计入预算/单资产测绘上限/out_of_scope 只记 fact 不 spawn"}
      cred-obtained: {action: "登记 creds(kind=session) → 触发 authz-diff 候选（批次 4 起）", guardrails: ""}
      scope-amended: {action: "amend-scope 落账（amendment_of 链+approvals 强制）→ tanyin-egress compile 重编译 ACL/DNS pinning/OOB 白名单 → out_of_scope 资产复判（转正则子矩阵初始化）→ canary 复测", guardrails: "修订未经审批=账本级 REJECT；修订史进报告守门声明"}
    exit:
      assert:
        - {cmd: "ledger-converge-check", expect: "converged | budget-exhausted"}
      on_pass: P4
    note: "converged 与 budget-exhausted 皆为合法终态；后者置 degraded=true 进入 P4"
  P4:
    title: 汇总
    duty: >-
      四校验命令 → finding 合并（supersede+tombstone）→ 「-」「!」抽查 → POC 独立重放门
      （批次 4 起强制：fresh 隔离子代理只拿 EV 卡片盲重放，set-replay-state 三态落账）
      → 异常检测（批量置态与 fact 密度不符告警）
    exit:
      assert:
        - {cmd: "ledger-validate", expect: PASS}
        - {cmd: "ledger-verify-chain", expect: PASS}
        - {cmd: "ledger-hash-recheck", expect: PASS}
        - {cmd: "ledger-matrix-audit", expect: "抽查通过 且 无告警"}
        - {cmd: "ledger-replay-summary", expect: "无 REJECTED 未处置项（批次 4 前=SKIP，报告中披露）"}
      on_pass: P5
      on_fail: halt
  P5:
    title: 报告
    duty: >-
      tanyin-report 聚合器从 13 表确定性重建正文（模板+账本数据，零 LLM 方差；LLM 仅写执行摘要
      与修复建议叙述段，须引用 finding ID）→ report-draft.md（附「范围外观察」附录：
      out_of_scope facts 列示供客户扩授权决策，接 §5.4 边界生长闭环）
    exit:
      assert:
        - {cmd: "ledger-terminal-gate", expect: "矩阵无空格 | degraded 披露清单完备"}
        - {cmd: "tanyin-report --lint", expect: "schema lint+脱敏检查 PASS"}
        - {cmd: "ledger-redact-scan --target report/", expect: "占位符零泄漏"}
      on_pass: P5.5
      on_fail: halt
  P5.5:
    title: 签发门
    duty: "人审 → ledger-approve（command_hash 绑定聚合产物文件哈希）→ report-signed.md"
    exit:
      assert:
        - {cmd: "ledger-approve --verify-signoff", expect: "approvals 存在对应 approved 行"}
      on_pass: P6.0
    note: "未签发报告禁止导出（cli 层：导出命令校验签发行）"
  P6.0:
    title: 清理门
    duty: >-
      ledger-cleanup-checklist 从 timeline 提取全部外部副作用写操作（revert_cmd 非空行）→ 逆序执行
      revert_cmd；纯账本状态行无需回滚 +结果验证 → 全核销或人工豁免（approvals 落账）
      → cleanup.md 清理声明附报告
    exit:
      assert:
        - {cmd: "ledger-cleanup-checklist --verify", expect: "全部 reverted 或 豁免行齐备"}
      on_pass: P6
  P6:
    title: 沉淀
    duty: >-
      脱敏提取（域名→CLIENT-NN，IP/凭据→占位符）→ 反向验证（session 出现过的域名/IP/凭据/token
      在草稿中零命中）→ 用户审批 → 写入 knowledge（precedents/entities/graph.ndjson）→ lint 保鲜信号
    exit:
      assert:
        - {cmd: "ledger-approve --knowledge", expect: approved}
        - {cmd: "tanyin-redact --reverse-verify", expect: "零命中"}
      on_pass: END
back_edges:
  - {from: P3, to: P4, when: budget-exhausted, mode: degraded}
  - {from: P3, to: P3, when: "asset-added | cred-obtained | scope-amended", type: event}
  - {from: P4, to: P4, when: "重放=REPAIRED（修复 POC 卡片后重放）", max_retry: 2}
```

- [ ] **Step 4: 实现解析器**（新建 `cli/ledger/phases_engine.py`，本任务只写头部+解析部分）

```python
# -*- coding: utf-8 -*-
"""tanyin-phases 引擎库（批次 3）——phases.yaml 确定性状态机运算（铁律 7 允许类 1）。
子命令实现按任务渐进落位（T2 validate / T3 gate / T6 restart / T7 resume-kit / T8 cached /
T5 rebuild-state）；dispatch 在 T2 随入口一并接通。
契约：contracts/04（yaml schema）+ phases/PROTOCOL.md（断言→命令调用协议/常驻集清单）。"""
import io, os, re, shlex, sys
from contextlib import redirect_stdout, redirect_stderr

from . import core
from .core import GATE_ORDER

DEFAULT_YAML = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "phases", "phases.yaml")


class PhasesSyntaxError(ValueError):
    """受限 YAML 子集语法外输入（fail-closed，不猜）。"""


def _strip_comment(line):
    out, q = [], None
    for i, ch in enumerate(line):
        if q:
            out.append(ch)
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch; out.append(ch)
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _split_flow(body):
    parts, depth, q, cur = [], 0, None, []
    for ch in body:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch; cur.append(ch)
        elif ch in "[{":
            depth += 1; cur.append(ch)
        elif ch in "]}":
            depth -= 1; cur.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur))
    return [p for p in (x.strip() for x in parts) if p]


def _unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _parse_flow(tok):
    tok = tok.strip()
    if tok.startswith("{") and tok.endswith("}"):
        body = tok[1:-1].strip()
        if not body:
            return {}
        m = {}
        for part in _split_flow(body):
            k, _, v = part.partition(":")
            m[_unquote(k)] = _parse_flow(v)
        return m
    if tok.startswith("[") and tok.endswith("]"):
        body = tok[1:-1].strip()
        return [] if not body else [_parse_flow(p) for p in _split_flow(body)]
    return _unquote(tok)


def parse_yaml(text):
    """受限子集：块映射/块列表/行内流映射/行内流列表/引号与裸标量/#注释/>- 与 | 块标量。"""
    lines = []
    for raw in text.splitlines():
        s = _strip_comment(raw)
        if not s.strip():
            continue
        indent = len(s) - len(s.lstrip(" "))
        if "\t" in s[:indent + 1]:
            raise PhasesSyntaxError("缩进禁 tab: %r" % raw)
        lines.append((indent, s.strip()))
    pos = [0]

    def parse_node(indent):
        if pos[0] >= len(lines) or lines[pos[0]][0] < indent:
            return None
        if lines[pos[0]][1] == "-" or lines[pos[0]][1].startswith("- "):
            return parse_seq(lines[pos[0]][0])
        return parse_map(lines[pos[0]][0])

    def parse_seq(indent):
        out = []
        while pos[0] < len(lines):
            ind, con = lines[pos[0]]
            if ind != indent or not (con == "-" or con.startswith("- ")):
                break
            item = con[1:].strip()
            pos[0] += 1
            if not item:
                out.append(parse_node(indent + 2))
            elif ":" in item and not item.startswith(("{", "[", "\"", "'")):
                out.append(_map_from(indent, item))
            else:
                out.append(_parse_flow(item))
        return out

    def _map_from(indent, first):
        m = {}
        k, _, v = first.partition(":")
        pos0 = pos[0]
        m[_unquote(k)] = _val(indent, v, pos0)
        while pos[0] < len(lines):
            ind, con = lines[pos[0]]
            if ind != indent or con.startswith("- "):
                break
            k, _, v = con.partition(":")
            pos[0] += 1
            m[_unquote(k)] = _val(indent, v, pos[0])
        return m

    def _val(indent, v, mark):
        v = v.strip()
        if not v:
            return parse_node(indent + 2)
        return _parse_flow(v)

    def parse_map(indent):
        m = {}
        while pos[0] < len(lines):
            ind, con = lines[pos[0]]
            if ind != indent or con.startswith("- "):
                break
            if ":" not in con:
                raise PhasesSyntaxError("映射行缺冒号: %r" % con)
            k, _, v = con.partition(":")
            pos[0] += 1
            v = v.strip()
            if v in (">", ">-", "|", "|-"):
                m[_unquote(k)] = _fold(indent, v)
            elif v:
                m[_unquote(k)] = _parse_flow(v)
            else:
                m[_unquote(k)] = parse_node(indent + 2)
        return m

    def _fold(indent, style):
        parts, base = [], None
        while pos[0] < len(lines) and lines[pos[0]][0] > indent:
            ind, con = lines[pos[0]]
            base = ind if base is None else base
            if ind < base:
                break
            parts.append(con)
            pos[0] += 1
        return " ".join(parts) if style.startswith(">") else "\n".join(parts)

    root = parse_node(0)
    if pos[0] != len(lines):
        raise PhasesSyntaxError("残余不可解析行: %r" % (lines[pos[0]],))
    if not isinstance(root, dict):
        raise PhasesSyntaxError("根节点须为映射")
    return root


def load_phases(path=None):
    p = path or DEFAULT_YAML
    if not os.path.isfile(p):
        raise PhasesSyntaxError("phases.yaml 未找到: " + p)
    with open(p, encoding="utf-8") as f:
        return parse_yaml(f.read())
```

注意 `_map_from` 里 `pos0` 未用可删（留给实现者自查 lint；此处贴的是可运行最小版——直接删掉 pos0/mark 参数亦可，测试不管内部形参）。

- [ ] **Step 5: 跑测试确认通过**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_phases_yaml -v`
Expected: 6 用例 PASS（test_loads_repo_yaml / test_constants_block / test_gate_asserts_shape / test_folded_duty_is_string / test_syntax_error_fail_closed / test_comment_and_quote）

- [ ] **Step 6: 回归+提交**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest discover -s tests && python3 tests/run_golden.py`
Expected: 全绿（本任务纯新增，无既有面改动）

```bash
git add phases/phases.yaml cli/ledger/phases_engine.py tests/test_phases_yaml.py
git commit -m "批次3 T1：phases.yaml 契约誊录+受限 YAML 子集解析器（stdlib 零依赖，fail-closed）"
```

---

## Task 2: schema 校验器 + tanyin-phases 入口（九门断言命令存在性）

**Files:**
- Modify: `cli/ledger/registry.py`（加 all_commands()）
- Modify: `cli/ledger/phases_engine.py`（validate_phases + dispatch 骨架 + cmd_validate）
- Create: `cli/tanyin-phases`、`cli/tanyin-phases.cmd`
- Test: `tests/test_phases_yaml.py`（追加 TestValidate 类）

**Interfaces:**
- Consumes: Task 1 的 load_phases；registry.lookup。
- Produces: `registry.all_commands() -> set[str]`（41 基名）；`phases_engine.validate_phases(data, known) -> list[str]`（错误清单，空=合法）；`phases_engine.dispatch(sub, goal_dir, rest) -> int`；CLI 用法 `tanyin-phases validate [--phases=<路径>]`（退出 0=合法 / 1=违规清单 / 2=用法或文件缺失）。这是 §10.3 静态验证③（phases.yaml schema 校验+九门断言命令存在性）的先行交付——批次 6 tanyin-selfcheck --static 可直接包装本子命令。

- [ ] **Step 1: 写失败测试**（test_phases_yaml.py 追加）

```python
class TestValidate(unittest.TestCase):
    def test_repo_yaml_valid(self):
        errs = pe.validate_phases(pe.load_phases(YAML_PATH), KNOWN)
        self.assertEqual(errs, [])

    def test_tampered_version(self):
        d = pe.load_phases(YAML_PATH); d["format_version"] = "3"
        self.assertTrue(any("format_version" in e for e in pe.validate_phases(d, KNOWN)))

    def test_tampered_constant(self):
        d = pe.load_phases(YAML_PATH); d["constants"]["restart_context_threshold"] = "0.9"
        self.assertTrue(any("restart_context_threshold" in e
                            for e in pe.validate_phases(d, KNOWN)))

    def test_unknown_assert_cmd(self):
        d = pe.load_phases(YAML_PATH)
        d["gates"]["P0"]["exit"]["assert"][0]["cmd"] = "ledger-no-such-cmd"
        self.assertTrue(any("不在命令面" in e for e in pe.validate_phases(d, KNOWN)))

    def test_missing_gate(self):
        d = pe.load_phases(YAML_PATH); del d["gates"]["P6.0"]
        self.assertTrue(any("P6.0" in e for e in pe.validate_phases(d, KNOWN)))

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)

    def test_cli_validate_exit_codes(self):
        import subprocess
        cli = os.path.join(ROOT, "cli", "tanyin-phases")
        r = subprocess.run([sys.executable, cli, "validate"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0)
        self.assertIn("PASS", r.stdout)
        with open(YAML_PATH, encoding="utf-8") as f:
            bad_text = f.read().replace("format_version: 2", "format_version: 3", 1)
        bad = os.path.join(self.td.name, "bad.yaml")
        with open(bad, "w", encoding="utf-8") as f:
            f.write(bad_text)
        r = subprocess.run([sys.executable, cli, "validate", "--phases=" + bad],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", r.stdout)
        self.assertIn("format_version", r.stdout)
```

`KNOWN` 在模块头 import 区之后取（P5/P6 断言引用 tanyin-report/tanyin-redact 两个非 ledger 入口，故并入已知面）：

```python
from ledger import registry

KNOWN = registry.all_commands() | {"tanyin-report", "tanyin-redact"}
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_phases_yaml -v`
Expected: 新增用例 FAIL（AttributeError: all_commands / validate_phases 不存在）

- [ ] **Step 3: registry.all_commands()**（cli/ledger/registry.py 追加）

```python
def all_commands():
    """枚举 41 命令基名（剥 ledger- 双前缀别名）——引擎断言存在性检查的单源。"""
    names = {"validate", "verify-chain", "next-id"}
    for m in _MODULES:
        try:
            mod = importlib.import_module("ledger." + m)
        except ImportError:
            continue
        for k in getattr(mod, "HANDLERS", {}):
            if not k.startswith("ledger-"):
                names.add(k)
    return names
```

- [ ] **Step 4: validate_phases + dispatch + 入口**（phases_engine.py 追加）

```python
FROZEN_CONSTANTS = {
    "restart_context_threshold": "0.75", "restart_every_n_rounds": "10",
    "storm_score_threshold_base": "0.5", "llm_association_quota": "5",
    "reversal_scan_quota": "3", "p4_sample_ratio": "0.2",
    "single_active_session": "true", "budget_dollars_enabled": "false",
}
EXTRA_TOOLS = {"tanyin-report", "tanyin-redact"}   # P5/P6 断言引用的非 ledger 入口


def validate_phases(data, known):
    errs = []
    if str(data.get("format_version")) != "2":
        errs.append("format_version!=2")
    if [str(x) for x in (data.get("states") or [])] != list(GATE_ORDER):
        errs.append("states != 九门全序 %s" % (GATE_ORDER,))
    if data.get("initial") != "P0":
        errs.append("initial != P0")
    c = data.get("constants") or {}
    if set(c) != set(FROZEN_CONSTANTS):
        errs.append("constants 键集 != 冻结 8 项")
    for k, v in FROZEN_CONSTANTS.items():
        if str(c.get(k)) != v:
            errs.append("constants.%s=%r != 冻结值 %r" % (k, c.get(k), v))
    gates = data.get("gates") or {}
    if set(gates) != set(GATE_ORDER):
        errs.append("gates 键集 != 九门（缺/多: %s）"
                    % sorted(set(GATE_ORDER) ^ set(gates)))
    for g in GATE_ORDER:
        ex = ((gates.get(g) or {}).get("exit") or {}).get("assert") or []
        if not ex:
            errs.append("gates.%s.exit.assert 空" % g)
        for i, a in enumerate(ex, 1):
            head = str(a.get("cmd", "")).split()[:1]
            if not head or head[0] not in known:
                errs.append("gates.%s.exit.assert[%d] 命令不在命令面: %r" % (g, i, a.get("cmd")))
    if len(data.get("back_edges") or []) != 3:
        errs.append("back_edges != 3 条")
    ev = ((gates.get("P3") or {}).get("events") or {})
    if set(ev) != {"asset-added", "cred-obtained", "scope-amended"}:
        errs.append("P3.events 三事件键缺失: %s" % sorted(set(ev)))
    return errs


def cmd_validate(rest):
    path = None
    for tok in rest:
        if tok.startswith("--phases="):
            path = tok.split("=", 1)[1]
        else:
            sys.stderr.write("用法: tanyin-phases validate [--phases=<路径>]\n"); return 2
    try:
        data = load_phases(path)
    except PhasesSyntaxError as e:
        sys.stderr.write("环境问题: %s\n" % e); return 2
    from . import registry
    known = registry.all_commands() | EXTRA_TOOLS
    errs = validate_phases(data, known)
    if errs:
        print("FAIL\tphases.yaml 违规 %d 项" % len(errs))
        for e in errs:
            print("  " + e)
        return 1
    n = sum(len(((data["gates"][g] or {}).get("exit") or {}).get("assert") or [])
            for g in GATE_ORDER)
    print("PASS\tphases.yaml 契约04合法 gates=9 asserts=%d constants=8 back_edges=3" % n)
    return 0


def dispatch(sub, goal_dir, rest):
    if sub == "validate":
        return cmd_validate(rest)
    sys.stderr.write("未知子命令: " + sub + chr(10)); return 2
```

入口 `cli/tanyin-phases`（照 tanyin-budgetctl 头部范式）：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tanyin-phases（批次 3）——phases.yaml 引擎 CLI 侧：确定性状态机运算（铁律 7 类 1）。
子命令：validate / gate / restart / resume-kit / cached / rebuild-state（后五个需 --goal-dir）。
退出码：0=通过 1=门禁失败（halt） 2=用法/环境（对齐 Strix）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ledger import phases_engine
from ledger.core import ensure_utf8_stdio

ensure_utf8_stdio()

USAGE = ("用法: tanyin-phases validate [--phases=P] | "
         "<gate|restart|resume-kit|cached|rebuild-state> --goal-dir D [参数]  "
         "(契约: contracts/04 + phases/PROTOCOL.md)")


def main(argv):
    if len(argv) < 2:
        sys.stderr.write(USAGE + chr(10)); return 2
    if argv[1] == "validate":
        return phases_engine.dispatch("validate", None, argv[2:])
    if len(argv) < 4 or argv[2] != "--goal-dir":
        sys.stderr.write(USAGE + chr(10)); return 2
    sub, gd, rest = argv[1], argv[3], argv[4:]
    if not os.path.isdir(gd):
        sys.stderr.write("环境问题: goal 目录不存在 " + gd + chr(10)); return 2
    return phases_engine.dispatch(sub, gd, rest)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

`cli/tanyin-phases.cmd`：照抄 cli/tanyin-budgetctl.cmd（`@py -3 "%~dp0tanyin-phases" %*` 形式，看现文件照抄改名）。

- [ ] **Step 5: 跑测试+金样化**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_phases_yaml -v && python3 tests/run_golden.py`
Expected: 全 PASS；再跑 `python3 cli/tanyin-phases validate > /tmp/pv.out && cp /tmp/pv.out tests/golden/phases-validate.norm`（金样基线；输出确定性——无时间戳无路径）

- [ ] **Step 6: 提交**

```bash
git add cli/ledger/registry.py cli/ledger/phases_engine.py cli/tanyin-phases cli/tanyin-phases.cmd tests/test_phases_yaml.py tests/golden/phases-validate.norm
git commit -m "批次3 T2：phases.yaml schema 校验器+九门断言命令存在性（registry.all_commands 单源）+tanyin-phases 入口"
```

---

## Task 3: gate 断言执行器（断言→命令调用协议落地）+ phases/PROTOCOL.md 落盘

**Files:**
- Modify: `cli/ledger/phases_engine.py`（_normalize_argv / judge / run_gate / dispatch 接 gate）
- Create: `phases/PROTOCOL.md`（本计划「批次 3 冻结接口」节的合订本全文落盘——逐字复制，勿改）
- Test: `tests/test_phases_gate.py`
- Test data: 复用 tests/fixtures/G-g1（timeline 已含 gate-exit:P0..P3 事件）

**Interfaces:**
- Consumes: load_phases/validate_phases（T1/T2）；registry.lookup；core.Session.gate_exit_seq。
- Produces: `phases_engine.run_gate(goal_dir, phase, ts, phases_path=None) -> int`；CLI `tanyin-phases gate --goal-dir D --phase <门> [--timestamp=T]`；timeline 事件词汇 gate-exit:/gate-fail:（PROTOCOL.md §1.3）。后续 T6 restart、T7 resume-kit 复用本任务的 `_current_gate(s)` 帮助函数（从 gate-exit 序推导当前门：无事件→P0；最大下标门为 P6→END；否则 GATE_ORDER[最大下标+1]）。

- [ ] **Step 1: 写失败测试**（新建 tests/test_phases_gate.py）

```python
# -*- coding: utf-8 -*-
"""批次 3 T3：gate 断言执行器——断言→命令调用协议（phases/PROTOCOL.md §1）。"""
import io, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import core, phases_engine as pe

FIX = os.path.join(HERE, "fixtures", "G-g1")
TAB = chr(9)
TS = "2026-09-24T08:00:00Z"


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def tl_events(self):
        ev = core.TABLES["timeline.tsv"].index("event")
        return [r[ev] for r in core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8)]

    def keep(self, pred):
        """删除满足 pred 的事件行、抹平全部 phase 门标并重算链——夹具 timeline 的 phase 列
        本身带 P0-P3（见 fixtures/G-g1/timeline.tsv 第 3 列），不抹会把 reached 抬到 P3，
        verify-chain 跳门检测随即要求 P1/P2 的 gate-exit 在场（test_query_check.py:545 同源语义）。"""
        p = os.path.join(self.gd, "timeline.tsv")
        ph = core.TABLES["timeline.tsv"].index("phase")
        rows = [r for r in core.read_tsv(p, 8) if not pred(r[3])]
        prev = core.GENESIS
        for r in rows:
            r[ph] = ""
            r[5] = prev
            r[6] = core.row_hash(prev, [r[j] for j in (0, 1, 2, 3, 4, 5, 7)])
            prev = r[6]
        core.write_tsv(p, rows)

    def add_scope_row(self, kind, matcher):
        from ledger import write_cmds
        write_cmds.HANDLERS["add-scope"](self.gd, [
            "--kind=" + kind, "--matcher=" + matcher, "--note=b3test",
            "--timestamp=" + TS])

    def call(self, *args):
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            code = pe.dispatch("gate", self.gd, list(args))
        return code, buf_o.getvalue(), buf_e.getvalue()


class TestGate(Base):
    def test_already_passed_idempotent(self):
        before = sum(1 for e in self.tl_events() if e.startswith("gate-exit:P0"))
        code, out, _ = self.call("--phase=P0", "--timestamp=" + TS)
        self.assertEqual(code, 0)
        self.assertIn("already-passed", out)
        after = sum(1 for e in self.tl_events() if e.startswith("gate-exit:P0"))
        self.assertEqual(before, after)   # 不重复落事件

    def test_gate_p0_runs_assertions_for_real(self):
        self.keep(lambda ev: ev.startswith("gate-exit:"))   # 抹掉全部过门事件+门标
        # 夹具 scope.tsv 只有 include 两行——P0 断言 ledger-scope-coverage 要求
        # include+exclude+oob 齐备，先经正规写命令补两行（顺带验链式延续）
        self.add_scope_row("exclude", "db.shop.example")
        self.add_scope_row("oob", "callbacks.example")
        code, out, err = self.call("--phase=P0", "--timestamp=" + TS)
        self.assertEqual(code, 0, out + err)
        evs = self.tl_events()
        self.assertTrue(any(e.startswith("gate-exit:P0 asserts=3 result=PASS") for e in evs))
        r = __import__("subprocess").run(
            [sys.executable, os.path.join(ROOT, "cli", "tanyin-ledger"),
             "verify-chain", "--goal-dir", self.gd], capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout)   # 新事件链一致且跳门检测通过

    def test_gate_fail_records_gate_fail_not_exit(self):
        self.keep(lambda ev: ev.startswith("gate-exit:"))
        # 破坏 P0 断言前提：删掉 oob scope 行（ledger-scope-coverage 会 FAIL）
        p = os.path.join(self.gd, "scope.tsv")
        rows = [r for r in core.read_tsv(p, 9) if r[1] != "oob"]
        core.write_tsv(p, rows)
        code, out, err = self.call("--phase=P0", "--timestamp=" + TS)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.startswith("gate-fail:P0") for e in self.tl_events()))
        self.assertFalse(any(e.startswith("gate-exit:P0") for e in self.tl_events()))

    def test_predecessor_required(self):
        self.keep(lambda ev: ev.startswith("gate-exit:"))
        code, out, _ = self.call("--phase=P2", "--timestamp=" + TS)   # P0/P1 未过
        self.assertEqual(code, 1)
        self.assertIn("前置门未过", out)
        self.assertEqual(len(self.tl_events()), 0)   # 零落账

    def test_p3_converge_degraded_mode(self):
        # 夹具已过 P0-P3；构造 budget-exhausted：goal requests 限额压到已用之下
        gi = core.TABLES["goals.tsv"].index("budget")
        p = os.path.join(self.gd, "goals.tsv")
        rows = core.read_tsv(p, 19)
        rows[0][gi] = "1;10;40"
        core.write_tsv(p, rows)
        self.keep(lambda ev: ev.startswith("gate-exit:P3"))
        code, out, err = self.call("--phase=P3", "--timestamp=" + TS)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(any(e.startswith("gate-exit:P3 asserts=1 result=PASS mode=degraded")
                            for e in self.tl_events()))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_phases_gate -v`
Expected: FAIL（dispatch 不认识 gate 子命令）

- [ ] **Step 3: 实现 run_gate**（phases_engine.py 追加；PROTOCOL.md §1 判定表逐行对应）

```python
SKIP_MARK = "批次 4 前=SKIP"


def _normalize_argv(tokens):
    out, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        if t.startswith("--") and "=" not in t and i + 1 < len(tokens) \
                and not tokens[i + 1].startswith("--"):
            out.append(t + "=" + tokens[i + 1]); i += 2
        else:
            out.append(t); i += 1
    return out


def _current_gate(s):
    seq, _ = s.gate_exit_seq()
    if not seq:
        return "P0"
    top = max(GATE_ORDER.index(g) for g in seq)
    return "END" if GATE_ORDER[top] == "P6" else GATE_ORDER[top + 1]


def _judge(expect, cmdline, code, out, err, s):
    name = cmdline.split()[0]
    if SKIP_MARK in expect:
        return "skip", "expect 载 SKIP（批次 4 转强制）"
    if name.endswith("converge-check"):
        tok = out.strip().splitlines()[0].strip() if out.strip() else ""
        if code == 0 and tok in ("converged", "budget-exhausted"):
            return "pass", ("mode=degraded" if tok == "budget-exhausted" else "")
        return "fail", "converge-check 输出=%r" % tok
    if name.endswith("matrix-gaps") and "--baseline" in cmdline:
        m = re.search(r"#baseline_rows=(\d+)", out)
        if code == 0 and "covered=true" in out and m and int(m.group(1)) > 0:
            return "pass", ""
        return "fail", "baseline=%s" % out.strip()[:60]
    if name.endswith("matrix-freeze") and code == 1:
        if "already-frozen" in (err + out) and any(
                r[core.TABLES["timeline.tsv"].index("event")].startswith("matrix-freeze")
                for r in s.rows("timeline.tsv")):
            return "pass", "already-frozen 幂等"
    if code == 2:
        return "env", (err or out).strip()[:80]
    return ("pass" if code == 0 else "fail"), (err or out).strip()[:80]


def _append_event(goal_dir, phase, event, ts):
    from . import registry
    h = registry.lookup("append-timeline")
    buf_o, buf_e = io.StringIO(), io.StringIO()
    with redirect_stdout(buf_o), redirect_stderr(buf_e):
        code = h(goal_dir, ["--actor=总控", "--phase=" + phase,
                            "--event=" + event, "--timestamp=" + ts])
    if code != 0:
        raise RuntimeError("append-timeline 失败: " + buf_e.getvalue())


def run_gate(goal_dir, phase, ts, phases_path=None):
    data = load_phases(phases_path)
    from . import registry
    errs = validate_phases(data, registry.all_commands() | EXTRA_TOOLS)
    if errs:
        sys.stderr.write("环境问题: phases.yaml 违规 %d 项\n" % len(errs)); return 2
    if phase not in GATE_ORDER:
        sys.stderr.write("用法错误: --phase 不在九门\n"); return 2
    if not ts:
        sys.stderr.write("用法错误: --timestamp 必填（ISO8601）\n"); return 2
    s = core.Session(goal_dir)
    seq, _ = s.gate_exit_seq()
    if phase in seq:
        print("OK" + chr(9) + "gate:%s already-passed" % phase); return 0
    for prev in GATE_ORDER[:GATE_ORDER.index(phase)]:
        if prev not in seq:
            print("REJECT" + chr(9) + "gate" + chr(9) + "前置门未过: " + prev)
            return 1
    asserts = data["gates"][phase]["exit"]["assert"]
    skipped, degraded = 0, False
    for a in asserts:
        cmdline, expect = str(a.get("cmd", "")), str(a.get("expect", ""))
        tokens = shlex.split(cmdline)
        h = registry.lookup(tokens[0])
        if h is None:
            _append_event(goal_dir, phase, "gate-fail:%s assert=%s reason=未知命令" % (phase, tokens[0]), ts)
            print("FAIL gate:%s 未知命令 %s" % (phase, tokens[0])); return 1
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            code = h(goal_dir, _normalize_argv(tokens[1:]))
        st, detail = _judge(expect, cmdline, code, buf_o.getvalue(), buf_e.getvalue(), s)
        if st == "env":
            print("ENV-HALT gate:%s assert=%s %s" % (phase, tokens[0], detail)); return 2
        if st == "skip":
            skipped += 1; continue
        if "mode=degraded" in detail:
            degraded = True
        if st == "fail":
            _append_event(goal_dir, phase,
                          "gate-fail:%s assert=%s reason=%s" % (phase, tokens[0], detail or "exit!=0"), ts)
            print("FAIL gate:%s assert=%s %s" % (phase, tokens[0], detail)); return 1
    ev = "gate-exit:%s asserts=%d result=PASS" % (phase, len(asserts))
    if skipped:
        ev += " skip=%d" % skipped
    if degraded:
        ev += " mode=degraded"
    _append_event(goal_dir, phase, ev, ts)
    print("OK" + chr(9) + "gate:%s %s" % (phase, ev))
    return 0
```

dispatch 追加：`if sub == "gate": 解析 --phase=/--timestamp=（其余 token 报用法 2）→ run_gate(goal_dir, phase, ts, None)`。

- [ ] **Step 4: 落盘 phases/PROTOCOL.md**：把本计划「批次 3 冻结接口」节 ~~~markdown 围栏内的全文逐字复制为文件（含 version: b3-frozen-1 头）。

- [ ] **Step 5: 跑测试确认通过+全量回归**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_phases_gate -v && python3 -m unittest discover -s tests && python3 tests/run_golden.py`
Expected: 全 PASS（夹具未被改动——测试只动临时目录拷贝）

- [ ] **Step 6: 金样化 already-passed 输出并提交**

Run: `python3 cli/tanyin-phases gate --goal-dir tests/fixtures/G-g1 --phase P4 --timestamp=2026-09-24T08:00:00Z`（夹具已过 P0-P3，P4 前置满足但夹具无 P4 断言通过态——预期 gate 真跑 P4 断言；改用 `--phase=P0` 得 already-passed 输出）→ 把 already-passed 单行存 `tests/golden/phases-gate-p0.norm`。

```bash
git add cli/ledger/phases_engine.py phases/PROTOCOL.md tests/test_phases_gate.py tests/golden/phases-gate-p0.norm
git commit -m "批次3 T3：gate 断言执行器——断言→命令调用协议落地+gate-exit/gate-fail 事件+PROTOCOL.md 接口冻结"
```

---
## Task 4: state.md v2 行结构冻结 + checkpoint 升级（200 行硬顶/原子写/单活跃会话锁）

**Files:**
- Create: `cli/ledger/state_md.py`
- Modify: `cli/ledger/write_cmds.py`（重写 `_checkpoint`，约 :846-872；文末探知注记 6 同步改写）
- Test: `tests/test_state_md.py`
- Modify: `tests/golden/write-checkpoint.state`（金样有意刷新——旧三行格式作废）+ `tests/run_golden.py`（VALS 补 --session=golden-s 一项，夹具驱动参数非命令面改动）

**Interfaces:**
- Consumes: 02a §13 checkpoint（签名 + 终审补全 5「state.md 行结构批次 3 冻结」授权）；`query_cmds.latest_intents/unconsumed_facts/matrix_gap_cells/budget_tree`（snapshot 投影）。
- Produces: **state.md v2 冻结格式**（本任务即接口冻结动作）：

```
revision: <int>            # 单调递增；state-rebuild 对账基准=timeline 行数（既有口径不变）
goal: <G-…>
phase: <P0..P6|空>         # 九门枚举（GATES 单源）
round: <int>               # P3 轮次（⓪步自增传入；非 P3=0）
session: <id>              # 活跃会话锁持有者
session_status: <active|released>
spawn: <fresh|auto|manual> # 本 revision 产生方式（managed-restart 记 auto/manual，普通轮 fresh）
updated: <ISO8601>
resume_kit: resume-kit.md  # 恢复注入白名单入口（T7 生成）
snapshot: intents_pending=<n>;facts_unconsumed=<n>;matrix_gaps=<n>;budget_token_left=<n|空>
--- handoff ---
<自由文本 ≤190 行（总行数含固定段硬顶 200）>
```

库接口（state_md.py，write_cmds 与 phases_engine 共用单一实现）：`parse_state(path) -> (fields dict|None, handoff list[str], errs list[str])`；`write_state(path, fields, handoff) -> None`（超 200 行 raise ValueError；tmp+os.replace 原子替换）；`would_overflow(handoff) -> bool`（写前预检）；`snapshot_from_session(s) -> str`（账本确定性投影）。checkpoint 新参数：`--session=<id>`（必填）、`--release`（旗标）、`--round=<int>`、`--spawn=<fresh|auto|manual>`、`--note=<handoff 文本，\n 分行>`；既有 `--phase/--event/--timestamp` 保留。

- [ ] **Step 1: 写失败测试**（新建 tests/test_state_md.py）

```python
# -*- coding: utf-8 -*-
"""批次 3 T4/T5：state.md v2（结构冻结/200 行硬顶/原子写/单活跃会话锁）+ state-rebuild 对账。"""
import io, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import core, state_md, write_cmds

FIX = os.path.join(HERE, "fixtures", "G-g1")
TAB = chr(9)
TS = "2026-09-24T09:00:00Z"


def snap_all(gd):
    out = {}
    for t in core.TABLES:
        p = os.path.join(gd, t)
        out[t] = open(p, "rb").read() if os.path.exists(p) else None
    for extra in ("state.md", "resume-kit.md"):
        p = os.path.join(gd, extra)
        out[extra] = open(p, "rb").read() if os.path.exists(p) else None
    return out


def tl_events(gd):
    ev = core.TABLES["timeline.tsv"].index("event")
    return [r[ev] for r in core.read_tsv(os.path.join(gd, "timeline.tsv"), 8)]


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def ck(self, *args):
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            code = write_cmds.HANDLERS["checkpoint"](self.gd, list(args))
        return code, buf_o.getvalue(), buf_e.getvalue()

    def state_path(self):
        return os.path.join(self.gd, "state.md")

    def read_state(self):
        return state_md.parse_state(self.state_path())

    def events(self):
        return tl_events(self.gd)

    def snap(self):
        return snap_all(self.gd)


class TestCheckpointV2(Base):
    def test_writes_frozen_structure(self):
        code, out, _ = self.ck("--session=s-1", "--phase=P3", "--round=4",
                               "--note=line1\nline2", "--timestamp=" + TS)
        self.assertEqual(code, 0)
        fields, handoff, errs = self.read_state()
        self.assertEqual(errs, [])
        self.assertEqual(list(fields), state_md.KEY_ORDER)
        self.assertEqual(fields["revision"], "1")
        self.assertEqual(fields["session"], "s-1")
        self.assertEqual(fields["session_status"], "active")
        self.assertEqual(fields["spawn"], "fresh")
        self.assertEqual(fields["phase"], "P3")
        self.assertEqual(fields["round"], "4")
        self.assertEqual(handoff, ["line1", "line2"])
        self.assertTrue(fields["snapshot"].startswith("intents_pending=1;"))  # 夹具 INT-g1-0002=pending

    def test_revision_monotonic_and_timeline_event(self):
        self.ck("--session=s-1", "--timestamp=" + TS)
        code, out, _ = self.ck("--session=s-1", "--timestamp=" + TS)
        self.assertEqual(code, 0)
        self.assertIn("revision=2", out)
        self.assertTrue(any(e.startswith("checkpoint revision=2") for e in self.events()))

    def test_single_active_session_lock(self):
        self.ck("--session=s-1", "--timestamp=" + TS)
        before = self.snap()
        code, _, err = self.ck("--session=s-2", "--timestamp=" + TS)
        self.assertEqual(code, 1)
        self.assertIn("单活跃会话", err)
        self.assertEqual(self.snap(), before)   # 零变更（timeline 也不动——预检前置）

    def test_release_then_takeover(self):
        self.ck("--session=s-1", "--timestamp=" + TS)
        code, _, _ = self.ck("--session=s-1", "--release", "--timestamp=" + TS)
        self.assertEqual(code, 0)
        fields, _, errs = self.read_state()
        self.assertEqual(fields["session_status"], "released")
        self.assertEqual(fields["revision"], "2")
        code, out, _ = self.ck("--session=s-2", "--timestamp=" + TS)   # 已释放可接管
        self.assertEqual(code, 0)
        self.assertIn("revision=3", out)

    def test_same_session_recheckpoint_ok(self):
        self.ck("--session=s-1", "--timestamp=" + TS)
        code, _, _ = self.ck("--session=s-1", "--round=2", "--timestamp=" + TS)
        self.assertEqual(code, 0)   # 同 session 每轮可重打（否则首锁卡死全部轮次）

    def test_200_line_hard_cap(self):
        note = "\n".join("h%d" % i for i in range(300))
        before = self.snap()
        code, _, err = self.ck("--session=s-1", "--note=" + note, "--timestamp=" + TS)
        self.assertEqual(code, 1)
        self.assertIn("200", err)
        self.assertFalse(os.path.exists(self.state_path()))
        self.assertEqual(self.snap(), before)   # 预检前置=timeline 也零变更

    def test_atomic_write_no_tmp_leftover(self):
        self.ck("--session=s-1", "--timestamp=" + TS)
        self.assertFalse(os.path.exists(self.state_path() + ".tmp"))
        self.assertTrue(os.path.isfile(self.state_path()))

    def test_tier0_no_goal_reject(self):
        os.remove(os.path.join(self.gd, "goals.tsv"))
        code, _, err = self.ck("--session=s-1", "--timestamp=" + TS)
        self.assertEqual(code, 1)
        self.assertIn("Tier0", err)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_state_md -v`
Expected: FAIL（state_md 模块不存在；现 checkpoint 无 --session）

- [ ] **Step 3: 实现 state_md.py**

```python
# -*- coding: utf-8 -*-
"""state.md v2 冻结格式（批次 3 接口，02a 终审补全 5 授权冻结）。
职责单一：键序/解析/原子写/200 行硬顶。语义（锁/对账/重建）在 write_cmds 与 phases_engine。"""
import os

from . import core

KEY_ORDER = ["revision", "goal", "phase", "round", "session", "session_status",
             "spawn", "updated", "resume_kit", "snapshot"]
HEADER = "--- handoff ---"
MAX_LINES = 200
SESSION_STATUS = {"active", "released"}
SPAWN_VALUES = {"fresh", "auto", "manual"}


def parse_state(path):
    """→ (fields|None, handoff 行列表, errs)。文件缺失=(None, [], [])。
    固定段逐行 key: value（沿 check_cmds.h_state_rebuild 既有 revision 解析范式扩展）。"""
    if not os.path.isfile(path):
        return None, [], []
    fields, handoff, errs, in_body = {}, [], [], False
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    if len(lines) > MAX_LINES:
        errs.append("state.md 行数 %d 超硬顶 %d" % (len(lines), MAX_LINES))
    for ln in lines:
        if ln.strip() == HEADER:
            in_body = True
            continue
        if in_body:
            handoff.append(ln)
            continue
        k, sep, v = ln.partition(":")
        if not sep:
            errs.append("固定段畸形行: %r" % ln)
            continue
        fields[k.strip()] = v.strip()
    if fields and list(fields) != KEY_ORDER:
        errs.append("固定段键集/键序不符: %s" % list(fields))
    if fields and not errs:
        if not fields["revision"].isdigit():
            errs.append("revision 非整数: %r" % fields["revision"])
        if fields["session_status"] not in SESSION_STATUS:
            errs.append("session_status 不在 {active,released}")
        if fields["spawn"] not in SPAWN_VALUES:
            errs.append("spawn 不在 {fresh,auto,manual}")
        if fields["phase"] and fields["phase"] not in core.GATE_ORDER:
            errs.append("phase 不在九门: %r" % fields["phase"])
    return fields, handoff, errs


def snapshot_from_session(s):
    from . import query_cmds as q
    pend = sum(1 for r in q.latest_intents(s).values()
               if r[q._idx("intents.tsv", "status")] == "pending")
    un = len(q.unconsumed_facts(s))
    gaps = len(q.matrix_gap_cells(s))
    t = q.budget_tree(s)
    left = ""
    if t["goal"] and t["goal"]["limit"]["token"] is not None:
        left = "%d" % int(t["goal"]["limit"]["token"] - t["goal"]["used"]["token"])
    return "intents_pending=%d;facts_unconsumed=%d;matrix_gaps=%d;budget_token_left=%s" \
        % (pend, un, gaps, left)


def would_overflow(handoff):
    return 1 + len(KEY_ORDER) + 1 + len([h for h in handoff]) > MAX_LINES


def write_state(path, fields, handoff):
    body = ["%s: %s" % (k, fields[k]) for k in KEY_ORDER] + [HEADER] + list(handoff)
    if len(body) > MAX_LINES:
        raise ValueError("state.md 超行数硬顶 %d（当前 %d）——压缩 handoff"
                         % (MAX_LINES, len(body)))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:   # LF 字节纪律
        f.write("\n".join(body) + "\n")
    os.replace(tmp, path)   # kill -9 半写兜底：要么旧版要么新版，无第三态
```

- [ ] **Step 4: 重写 _checkpoint**（write_cmds.py :846-872 替换；头部 import 追加 `from . import state_md`）

```python
def _checkpoint(goal_dir, rest):
    args = _parse(rest, {"phase", "event", "timestamp", "session", "release",
                         "round", "note", "spawn"})
    _req(args, ["timestamp", "session"])
    ctx = Ctx(goal_dir)
    ctx.tier0()
    phase = args.get("phase", "")
    if phase and phase not in GATES:
        raise Reject("phase 不在九门枚举 {P0,P1,P2,P3,P4,P5,P5.5,P6.0,P6}: " + phase)
    release = bool(args.get("release"))
    spawn = args.get("spawn", "fresh")
    if spawn not in ("fresh", "auto", "manual"):
        raise Reject("spawn 不在 {fresh,auto,manual}: " + spawn)
    handoff = [ln for ln in (args.get("note") or "").split("\n") if ln != ""]
    if state_md.would_overflow(handoff):   # 预检前置：拒收=timeline 也零变更
        raise Reject("state.md 将超行数硬顶 200——压缩 handoff")
    sp = os.path.join(ctx.s.dir, "state.md")
    fields, _, perrs = state_md.parse_state(sp)
    if perrs:
        raise Reject("state.md 损坏（先 tanyin-phases rebuild-state 对账重建）: " + perrs[0])
    if fields and fields["session_status"] == "active" \
            and fields["session"] != args["session"]:
        raise Reject("单活跃会话：session=%s 持锁未释放（接管走 tanyin-phases restart --spawn manual）"
                     % fields["session"])
    rev = (int(fields["revision"]) if fields else 0) + 1
    # timeline 先行（第一事实源）：kill -9 撕裂态=timeline 领先 state →
    # state-rebuild FAIL → rebuild-state 以 timeline 为准重建（设计 §4.1 快照损坏=对账重建）
    ev = "checkpoint revision=%d%s" % (rev, " release" if release else "")
    if args.get("event"):
        ev += " " + args["event"]
    ctx.event(args["timestamp"], ev, actor="总控", phase=phase)
    ctx.commit({"timeline.tsv"})
    new_fields = {
        "revision": str(rev),
        "goal": ctx.rows("goals.tsv")[0][0] if ctx.rows("goals.tsv") else "",
        "phase": phase,
        "round": args.get("round", "0"),
        "session": args["session"],
        "session_status": "released" if release else "active",
        "spawn": spawn,
        "updated": args["timestamp"],
        "resume_kit": "resume-kit.md",
        "snapshot": state_md.snapshot_from_session(ctx.s),
    }
    state_md.write_state(sp, new_fields, handoff)
    print("OK" + TAB + "revision=%d" % rev)
    return 0
```

- [ ] **Step 5: 跑测试+刷新金样+全量回归**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_state_md -v`（先绿）
Run: `python3 tests/run_golden.py`——预期 write-checkpoint 金样 FAIL（旧格式，**有意刷新**）：run_golden.py 的 VALS 字典补 `"--session": "golden-s"` 一项后，把新 state.md 字节存 `tests/golden/write-checkpoint.state`（run_golden.py 的金样更新机制照其现有 --bless/手工流程走）。刷新后复跑全绿。

- [ ] **Step 6: 提交**

```bash
git add cli/ledger/state_md.py cli/ledger/write_cmds.py tests/test_state_md.py tests/golden/write-checkpoint.state tests/run_golden.py
git commit -m "批次3 T4：state.md v2 行结构冻结（10 固定键+handoff≤200 行硬顶+原子写）+checkpoint 单活跃会话锁"
```

---

## Task 5: state-rebuild v2 对账升级 + tanyin-phases rebuild-state（对账重建）

**Files:**
- Modify: `cli/ledger/check_cmds.py`（h_state_rebuild :148-175 扩展）
- Modify: `cli/ledger/phases_engine.py`（rebuild_state + dispatch 接线）
- Test: `tests/test_state_md.py`（追加 TestRebuild 类）

**Interfaces:**
- Consumes: state_md.parse_state/snapshot_from_session/write_state（T4）；core.Session；T3 的 `_current_gate`。
- Produces: `tanyin-phases rebuild-state --goal-dir D --timestamp=T [--note=…]`（退出 0=重建成功输出 revision=N；1=timeline 链断拒绝重建——链断必须人工，halt）。state-rebuild 新对账项：固定段键齐/枚举合法/行数≤200/revision==timeline 行数（既有）/**snapshot 与账本重算一致**（新增——「对账」的实质）。输出首行 `PASS\trevision=<n>` 不变（金样 read-state-rebuild.norm 不回红；追加信息放第二行）。

- [ ] **Step 1: 写失败测试**（test_state_md.py 追加）

```python
class TestRebuild(Base):
    def _rebuild_check(self):
        from ledger import check_cmds
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = check_cmds.HANDLERS["state-rebuild"](self.gd, [])
        return code, buf.getvalue()

    def test_state_rebuild_pass_after_checkpoint(self):
        self.ck("--session=s-1", "--phase=P3", "--timestamp=" + TS)
        code, out = self._rebuild_check()
        self.assertEqual(code, 0)
        self.assertIn("PASS\trevision=", out)

    def test_state_rebuild_detects_snapshot_drift(self):
        self.ck("--session=s-1", "--phase=P3", "--timestamp=" + TS)
        # 撕裂态 B 等价构造：checkpoint 后账本又前进一行（timeline 领先 state）
        write_cmds.HANDLERS["append-timeline"](self.gd, [
            "--actor=CLI", "--phase=", "--event=drift", "--timestamp=" + TS])
        code, out = self._rebuild_check()
        self.assertEqual(code, 1)
        self.assertIn("rebuild-state", out)

    def test_rebuild_state_repairs(self):
        self.ck("--session=s-1", "--phase=P3", "--timestamp=" + TS)
        os.remove(self.state_path())   # 撕裂态 C：state.md 缺失
        from ledger import phases_engine as pe
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pe.dispatch("rebuild-state", self.gd, ["--timestamp=" + TS])
        self.assertEqual(code, 0, buf.getvalue())
        fields, _, errs = self.read_state()
        self.assertEqual(errs, [])
        self.assertEqual(fields["session_status"], "released")   # 重建=锁释放（防双活）
        self.assertEqual(fields["spawn"], "manual")
        code, out = self._rebuild_check()   # 重建后再对账=PASS
        self.assertEqual(code, 0)

    def test_rebuild_state_clears_tmp_leftover(self):
        self.ck("--session=s-1", "--timestamp=" + TS)
        open(self.state_path() + ".tmp", "w").write("torn")   # 撕裂态 A：tmp 残留
        from ledger import phases_engine as pe
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pe.dispatch("rebuild-state", self.gd, ["--timestamp=" + TS])
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.state_path() + ".tmp"))

    def test_rebuild_state_refuses_broken_chain(self):
        p = os.path.join(self.gd, "timeline.tsv")
        rows = core.read_tsv(p, 8)
        rows[2][3] = "tampered"   # 破坏中间事件→断链
        core.write_tsv(p, rows)
        from ledger import phases_engine as pe
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pe.dispatch("rebuild-state", self.gd, ["--timestamp=" + TS])
        self.assertEqual(code, 1)
        self.assertIn("链", buf.getvalue())
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_state_md -v`
Expected: 新增类 FAIL（现 state-rebuild 只查 revision；dispatch 无 rebuild-state）

- [ ] **Step 3: 升级 h_state_rebuild**（check_cmds.py :148-175 替换；头部 `from . import state_md`）

```python
def h_state_rebuild(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or args:
        raise UsageError("state-rebuild 无参数")
    s = core.Session(goal_dir)
    chain_err = _chain_fail(s)
    if chain_err:
        print("FAIL")
        print(chain_err)
        return 1
    revision = len(s.rows("timeline.tsv"))
    st_path = os.path.join(goal_dir, "state.md")
    if not os.path.isfile(st_path):
        print("PASS\trevision=%d\tstate.md=absent" % revision)
        return 0
    fields, handoff, errs = state_md.parse_state(st_path)
    if errs:
        print("FAIL")
        for e in errs[:5]:
            print(e + "（tanyin-phases rebuild-state 对账重建）")
        return 1
    if int(fields["revision"]) != revision:
        print("FAIL")
        print("state.md revision=%s 与账本重建 revision=%d 不一致（tanyin-phases rebuild-state 对账重建）"
              % (fields["revision"], revision))
        return 1
    expect_snap = state_md.snapshot_from_session(s)
    if fields["snapshot"] != expect_snap:
        print("FAIL")
        print("snapshot 漂移: state=%r 账本重算=%r（tanyin-phases rebuild-state 对账重建）"
              % (fields["snapshot"], expect_snap))
        return 1
    print("PASS\trevision=%d" % revision)
    print("state.md v2 对账一致 session=%s phase=%s" % (fields["session"], fields["phase"]))
    return 0
```

- [ ] **Step 4: 实现 rebuild_state**（phases_engine.py 追加；dispatch 接 rebuild-state 解析 --timestamp= 必填/--note= 可选）

```python
def rebuild_state(goal_dir, ts, note=""):
    s = core.Session(goal_dir)
    ok, bad = s.verify_chain()
    if not ok:
        print("FAIL rebuild-state: timeline 断链行=%d——链断不可自愈，人工处置（halt）" % bad)
        return 1
    from . import state_md
    gate = _current_gate(s)
    fields = {
        "revision": str(len(s.rows("timeline.tsv"))),
        "goal": s.rows("goals.tsv")[0][0] if s.rows("goals.tsv") else "",
        "phase": "" if gate == "P0" else gate,
        "round": "0",
        "session": "rebuilt",
        "session_status": "released",   # 重建=锁必须释放（防双活；接管者走 checkpoint/restart 重取锁）
        "spawn": "manual",
        "updated": ts,
        "resume_kit": "resume-kit.md",
        "snapshot": state_md.snapshot_from_session(s),
    }
    handoff = ["rebuilt from ledger @ " + ts] + ([note] if note else [])
    tmp = os.path.join(goal_dir, "state.md.tmp")
    if os.path.exists(tmp):
        os.remove(tmp)   # 撕裂态 A 清理：tmp 残留一并扫除
    try:
        state_md.write_state(os.path.join(goal_dir, "state.md"), fields, handoff)
    except ValueError as e:
        print("FAIL rebuild-state: " + str(e))
        return 1
    print("OK\trebuild-state\trevision=%s" % fields["revision"])
    return 0
```

- [ ] **Step 5: 跑测试+金样回归**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_state_md -v && python3 tests/run_golden.py`
Expected: 全 PASS（read-state-rebuild.norm 首行未变；若金样比对含后续行则同步刷新该 .norm——同属有意刷新，commit 注明）。

- [ ] **Step 6: 提交**

```bash
git add cli/ledger/check_cmds.py cli/ledger/phases_engine.py tests/test_state_md.py tests/golden/read-state-rebuild.norm
git commit -m "批次3 T5：state-rebuild v2 对账（snapshot 漂移检测）+rebuild-state 对账重建（链断拒绝自愈/tmp 清扫）"
```

---

## Task 6: 受管重启（自动/兜底档 + 护栏四件套）

**Files:**
- Modify: `cli/ledger/phases_engine.py`（run_restart + RESTART_RATE_MINUTES/RESTART_TOKEN_COST 常量 + dispatch 接线）
- Test: `tests/test_managed_restart.py`

**Interfaces:**
- Consumes: 设计 §5.2 补充语义（护栏=计入预算/速率上限/单活跃会话/timeline 记 managed-restart 含 spawn 方式）；T4 checkpoint（--spawn/--session/--event）；registry 的 state-rebuild / budget-log / checkpoint 三个既有命令（restart 只编排既有命令，不自己写 TSV，链一致性由命令自保）。
- Produces: `tanyin-phases restart --goal-dir D --spawn auto|manual [--timestamp=T] [--session=S] [--rate-minutes=N] [--token-cost=C]`。模块常量 `RESTART_RATE_MINUTES = 10`、`RESTART_TOKEN_COST = 2000`（--rate-minutes/--token-cost 覆盖供 evals 重放；两常量缺契约源→探知项 G-3/G-4）。timeline 事件词：`managed-restart spawn=<auto|manual>[ takeover-of=<旧 session>]`（经 checkpoint --event 落账，actor=总控）。SKILL.md 第⑥节与 T10 phases/P3.md 消费本命令；T7 的 write_resume_kit 在函数尾接通。

护栏链（顺序执行，任一 REJECT=退出 1 且零副作用——预算流水/事件/锁一概不落）：

```
① verify-chain PASS（链断=拒绝重启，要求人工 halt）
② 速率上限：timeline 最近一条 managed-restart 事件时间戳距 --timestamp < rate_minutes 分钟
   → REJECT restart-rate-limit last=<ts>（防递归 spawn：重启→崩→重启循环）
③ 单活跃会话：state.md session_status=active 且 session≠本方 →
   auto：REJECT（自动档不得接管）；manual：须 state-rebuild 对账 PASS 才接管，
         事件记 takeover-of=<旧 session>（kill -9 后锁残留的兜底档；无跨平台进程存活
         探测——探知项 G-5，以对账通过+timeline 留痕为接管凭据）
④ 计入预算：budget-log --token-delta=<cost> --requests-delta=0 --hours-delta=0
   --dollars-delta=0 --scope=goal --note=managed-restart spawn=<spawn>（重启吃预算→
   重启循环最终触达 budget-exhausted 合法终态，护栏闭环）
⑤ checkpoint --spawn=<spawn> --session=<新> --event=managed-restart spawn=…（state.md v2 落 revision+锁）
⑥ resume-kit 重生成（T7 接通；本任务先留调用点注释锚）
```

- [ ] **Step 1: 写失败测试**（新建 tests/test_managed_restart.py）

```python
# -*- coding: utf-8 -*-
"""批次 3 T6：受管重启护栏四件套（速率上限/计入预算/单活跃会话/timeline 事件）。"""
import io, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import core, phases_engine as pe, state_md, write_cmds

FIX = os.path.join(HERE, "fixtures", "G-g1")
T0 = "2026-09-24T10:00:00Z"
T1 = "2026-09-24T10:05:00Z"   # 距 T0 5 分钟 < 10 分钟默认窗
T2 = "2026-09-24T10:20:00Z"   # 距 T0 20 分钟 > 窗


def snap_all(gd):
    out = {}
    for t in core.TABLES:
        p = os.path.join(gd, t)
        out[t] = open(p, "rb").read() if os.path.exists(p) else None
    for extra in ("state.md",):
        p = os.path.join(gd, extra)
        out[extra] = open(p, "rb").read() if os.path.exists(p) else None
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def restart(self, *args):
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            code = pe.dispatch("restart", self.gd, list(args))
        return code, buf_o.getvalue(), buf_e.getvalue()

    def events(self):
        ev = core.TABLES["timeline.tsv"].index("event")
        return [r[ev] for r in core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8)]

    def budget_last(self):
        return core.read_tsv(os.path.join(self.gd, "budget.tsv"), 8)[-1]

    def snap(self):
        return snap_all(self.gd)


class TestRestart(Base):
    def test_happy_path_writes_guardrails(self):
        code, out, err = self.restart("--spawn=auto", "--timestamp=" + T0)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(any(e.startswith("managed-restart spawn=auto") for e in self.events()))
        bl = self.budget_last()
        self.assertEqual(bl[5], "goal")
        self.assertIn("managed-restart spawn=auto", bl[6])
        self.assertEqual(bl[1], "2000")   # token_delta=RESTART_TOKEN_COST 计入预算
        f, _, errs = state_md.parse_state(os.path.join(self.gd, "state.md"))
        self.assertEqual(errs, [])
        self.assertEqual(f["spawn"], "auto")
        self.assertEqual(f["session_status"], "active")

    def test_rate_limit_second_restart_within_window(self):
        self.restart("--spawn=auto", "--timestamp=" + T0)
        before = self.snap()
        code, out, _ = self.restart("--spawn=auto", "--timestamp=" + T1)
        self.assertEqual(code, 1)
        self.assertIn("restart-rate-limit", out)
        self.assertEqual(self.snap(), before)   # 零副作用

    def test_rate_window_elapsed_ok(self):
        self.restart("--spawn=auto", "--timestamp=" + T0)
        code, out, err = self.restart("--spawn=auto", "--timestamp=" + T2)
        self.assertEqual(code, 0, out + err)

    def test_auto_cannot_takeover_active_lock(self):
        write_cmds.HANDLERS["checkpoint"](self.gd,
            ["--session=s-owner", "--phase=P3", "--timestamp=" + T0])
        before = self.snap()
        code, out, _ = self.restart("--spawn=auto", "--timestamp=" + T1)
        self.assertEqual(code, 1)
        self.assertIn("单活跃会话", out)
        self.assertEqual(self.snap(), before)

    def test_manual_takeover_with_rebuild_ok(self):
        write_cmds.HANDLERS["checkpoint"](self.gd,
            ["--session=s-owner", "--phase=P3", "--timestamp=" + T0])
        code, out, err = self.restart("--spawn=manual", "--timestamp=" + T2)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(any("takeover-of=s-owner" in e for e in self.events()))

    def test_broken_chain_refuses(self):
        p = os.path.join(self.gd, "timeline.tsv")
        rows = core.read_tsv(p, 8)
        rows[2][3] = "tampered"
        core.write_tsv(p, rows)
        code, out, _ = self.restart("--spawn=auto", "--timestamp=" + T0)
        self.assertEqual(code, 1)
        self.assertIn("链", out)

    def test_budget_reflects_restart_cost(self):
        from ledger import query_cmds
        before = query_cmds.budget_tree(core.Session(self.gd))["goal"]["used"]["token"]
        self.restart("--spawn=auto", "--timestamp=" + T0, "--token-cost=500")
        after = query_cmds.budget_tree(core.Session(self.gd))["goal"]["used"]["token"]
        self.assertEqual(after - before, 500)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_managed_restart -v`
Expected: FAIL（dispatch 不认识 restart）

- [ ] **Step 3: 实现 run_restart**（phases_engine.py 追加）

```python
RESTART_RATE_MINUTES = 10   # 探知项 G-3：契约 04 constants 冻结 8 项无此值；模块常量+参数覆盖
RESTART_TOKEN_COST = 2000  # 探知项 G-4：重启 token 成本口径缺源；默认 2000 可覆盖


def _parse_ts(tok):
    import datetime
    t = tok.strip()
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    dt = datetime.datetime.fromisoformat(t)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.timestamp()


def _last_restart_ts(s):
    ts_i = core.TABLES["timeline.tsv"].index("timestamp")
    ev_i = core.TABLES["timeline.tsv"].index("event")
    out = None
    for r in s.rows("timeline.tsv"):
        if r[ev_i].startswith("managed-restart"):
            out = r[ts_i]
    return out


def run_restart(goal_dir, spawn, ts, session=None, rate_minutes=None, token_cost=None):
    from . import registry, state_md
    if spawn not in ("auto", "manual"):
        sys.stderr.write("用法错误: --spawn 需 auto|manual\n")
        return 2
    if not ts:
        sys.stderr.write("用法错误: --timestamp 必填（ISO8601）\n")
        return 2
    s = core.Session(goal_dir)
    ok, bad = s.verify_chain()
    if not ok:
        print("REJECT\trestart\ttimeline 断链行=%d——人工处置（halt）" % bad)
        return 1
    rate = float(rate_minutes) if rate_minutes else RESTART_RATE_MINUTES
    last = _last_restart_ts(s)
    if last:
        delta_min = (_parse_ts(ts) - _parse_ts(last)) / 60.0
        if delta_min < rate:
            print("REJECT\trestart\trestart-rate-limit last=%s 距今 %.1f 分钟 < %.0f 分钟"
                  % (last, delta_min, rate))
            return 1
    sp = os.path.join(goal_dir, "state.md")
    fields, _, perrs = state_md.parse_state(sp)
    if perrs:
        print("REJECT\trestart\tstate.md 损坏：先 rebuild-state（%s）" % perrs[0])
        return 1
    takeover = ""
    if fields and fields["session_status"] == "active":
        if spawn == "auto":
            print("REJECT\trestart\t单活跃会话：auto 不得接管 active 锁 session=%s" % fields["session"])
            return 1
        buf = io.StringIO()
        with redirect_stdout(buf):
            rb = registry.lookup("state-rebuild")(goal_dir, [])
        if rb != 0:
            print("REJECT\trestart\tmanual 接管前置 state-rebuild 未过（先对账）: " + buf.getvalue())
            return 1
        takeover = " takeover-of=" + fields["session"]
    session = session or ("r-" + core.row_hash(ts, [spawn])[:8])
    cost = str(int(token_cost)) if token_cost else str(RESTART_TOKEN_COST)
    # ④ 计入预算（既有 budget-log，链一致）
    bl = registry.lookup("budget-log")
    b1, b2 = io.StringIO(), io.StringIO()
    with redirect_stdout(b1), redirect_stderr(b2):
        rc = bl(goal_dir, ["--token-delta=" + cost, "--requests-delta=0",
                           "--hours-delta=0", "--dollars-delta=0", "--scope=goal",
                           "--note=managed-restart spawn=" + spawn, "--timestamp=" + ts])
    if rc != 0:
        print("REJECT\trestart\tbudget-log 失败: " + b2.getvalue())
        return 1
    # ⑤ timeline 事件（经 checkpoint --event 落账）+ state.md v2
    gate = _current_gate(s)
    ck = registry.lookup("checkpoint")
    c1, c2 = io.StringIO(), io.StringIO()
    with redirect_stdout(c1), redirect_stderr(c2):
        rc = ck(goal_dir, ["--session=" + session, "--spawn=" + spawn,
                           "--phase=" + ("" if gate == "P0" else gate),
                           "--event=managed-restart spawn=" + spawn + takeover,
                           "--timestamp=" + ts])
    if rc != 0:
        print("REJECT\trestart\tcheckpoint 失败: " + c2.getvalue())
        return 1
    rev = state_md.parse_state(sp)[0]["revision"]
    # ⑥ T7 接通点：write_resume_kit(goal_dir, ts)
    print("OK\trestart\tspawn=%s\trevision=%s\tsession=%s" % (spawn, rev, session))
    return 0
```

dispatch 追加 `restart`（解析 --spawn/--timestamp/--session/--rate-minutes/--token-cost；未知参数=用法 2）。

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_managed_restart -v`
Expected: 7 用例 PASS

- [ ] **Step 5: 全量回归+提交**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest discover -s tests && python3 tests/run_golden.py`
Expected: 全绿

```bash
git add cli/ledger/phases_engine.py tests/test_managed_restart.py
git commit -m "批次3 T6：受管重启护栏四件套——速率上限/计入预算/单活跃会话锁（auto 禁接管+manual 对账接管）/timeline managed-restart 事件"
```

---
## Task 7: resume-kit 生成器（恢复注入白名单 + 先对账再干活）

**Files:**
- Modify: `cli/ledger/phases_engine.py`（write_resume_kit + dispatch 接线；并在 run_restart 尾部 ⑥ 接通调用）
- Test: `tests/test_resume_kit.py`
- Test data: `tests/golden/phases-resume-kit.norm`（fixture 上的内容基线）

**Interfaces:**
- Consumes: T3 `_current_gate`；core.Session.verify_chain；T8 的 cache 状态（本任务先内联 `cache_lines()`，T8 提为独立函数后共用——**实现顺序注意：把 cache_lines 直接写成 T8 接口的样子**：`cache_lines(s, goal_dir) -> list[(intent_id, SKIP|RUN)]`）。
- Produces: `tanyin-phases resume-kit --goal-dir D [--timestamp=T]` → 原子写 `<goal-dir>/resume-kit.md`（tmp+replace，LF）。退出 0=生成；1=链断拒绝生成。产物结构（生成器模板冻结）：

```
# resume-kit · 恢复注入白名单（先对账再干活）
goal: <G-…>
current_gate: <P0..P6|END>
updated: <ts>

## 0 对账（必须先过；任一失败=停止并人工，禁止跳到干活）
1. tanyin-ledger verify-chain --goal-dir <D>       → PASS 才继续
2. tanyin-ledger state-rebuild --goal-dir <D>      → FAIL 则 tanyin-phases rebuild-state 后复跑本条

## 1 注入白名单（新会话上下文只许进这些）
- state.md（handoff 与 snapshot）
- resume-kit.md（本文件）
- phases/<current_gate>.md（当前门方法论，单门单载）
- 四个查询摘要各一次（计数+top-N，禁全量回灌）：pending-intents / unconsumed-facts / matrix-gaps / budget-check

## 2 禁注入清单（铁律 2 上下文生命周期受管）
- 13 表 TSV 全量回灌 / 工件原文（artifacts/、*.raw）/ 子代理会话记录

## 3 幂等续跑判定（重入先查此表）
- <INT-…>  SKIP   # intent done 且 submissions/<id>/submission.json 在场
- <INT-…>  RUN
```

- [ ] **Step 1: 写失败测试**（新建 tests/test_resume_kit.py）

```python
# -*- coding: utf-8 -*-
"""批次 3 T7：resume-kit 生成——白名单注入清单/先对账/幂等字节一致。"""
import io, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import core, phases_engine as pe

FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T11:00:00Z"


class TestResumeKit(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def gen(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pe.dispatch("resume-kit", self.gd, list(args) or ["--timestamp=" + TS])
        return code, buf.getvalue()

    def read_kit(self):
        p = os.path.join(self.gd, "resume-kit.md")
        return open(p, encoding="utf-8").read() if os.path.exists(p) else None

    def test_generates_whitelist_content(self):
        code, out = self.gen()
        self.assertEqual(code, 0, out)
        kit = self.read_kit()
        self.assertIn("先对账再干活", kit)
        self.assertIn("current_gate: P4", kit)   # 夹具已过 P0-P3 → 下一门 P4
        self.assertIn("verify-chain", kit)
        self.assertIn("state-rebuild", kit)
        self.assertIn("phases/P4.md", kit)
        self.assertIn("pending-intents", kit)
        self.assertIn("禁注入", kit)
        self.assertIn("INT-g1-0001", kit)   # 夹具 done intent 进幂等表

    def test_idempotent_byte_identical(self):
        self.gen()
        first = self.read_kit()
        self.gen()
        self.assertEqual(self.read_kit(), first)   # 同账本+同 ts=字节一致（确定性投影）

    def test_broken_chain_refuses(self):
        p = os.path.join(self.gd, "timeline.tsv")
        rows = core.read_tsv(p, 8)
        rows[2][3] = "tampered"
        core.write_tsv(p, rows)
        code, out = self.gen()
        self.assertEqual(code, 1)
        self.assertIsNone(self.read_kit())

    def test_atomic_no_tmp(self):
        self.gen()
        self.assertFalse(os.path.exists(os.path.join(self.gd, "resume-kit.md.tmp")))

    def test_skip_table_reflects_submissions(self):
        os.makedirs(os.path.join(self.gd, "submissions", "INT-g1-0001"), exist_ok=True)
        with open(os.path.join(self.gd, "submissions", "INT-g1-0001", "submission.json"),
                  "w", encoding="utf-8") as f:
            f.write("{}")
        self.gen()
        kit = self.read_kit()
        self.assertRegex(kit, r"INT-g1-0001\s+SKIP")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_resume_kit -v`
Expected: FAIL（dispatch 不认识 resume-kit）

- [ ] **Step 3: 实现 write_resume_kit**（phases_engine.py 追加；cache_lines 签名按 T8 接口写）

```python
def cache_lines(s, goal_dir):
    """幂等续跑判定（设计 §5.2 补充语义）：intent done 且 submissions/<id>/submission.json
    存在→SKIP；其余（含 done 无工件）→RUN。确定性只读。"""
    from . import query_cmds as q
    out = []
    for key, r in sorted(q.latest_intents(s).items()):
        iid = key[0]
        if q._cell(r, "intents.tsv", "status") != "done":
            continue
        p = os.path.join(goal_dir, "submissions", iid, "submission.json")
        out.append((iid, "SKIP" if os.path.isfile(p) else "RUN"))
    return out


def write_resume_kit(goal_dir, ts):
    s = core.Session(goal_dir)
    ok, bad = s.verify_chain()
    if not ok:
        print("FAIL resume-kit: timeline 断链行=%d——先人工处置" % bad)
        return 1
    gate = _current_gate(s)
    goal = s.rows("goals.tsv")[0][0] if s.rows("goals.tsv") else ""
    lines = [
        "# resume-kit · 恢复注入白名单（先对账再干活）",
        "goal: " + goal,
        "current_gate: " + gate,
        "updated: " + ts,
        "",
        "## 0 对账（必须先过；任一失败=停止并人工，禁止跳到干活）",
        "1. tanyin-ledger verify-chain --goal-dir <D>       → PASS 才继续",
        "2. tanyin-ledger state-rebuild --goal-dir <D>      → FAIL 则 tanyin-phases rebuild-state 后复跑本条",
        "",
        "## 1 注入白名单（新会话上下文只许进这些）",
        "- state.md（handoff 与 snapshot）",
        "- resume-kit.md（本文件）",
        "- phases/" + gate + ".md（当前门方法论，单门单载）",
        "- 四个查询摘要各一次（计数+top-N，禁全量回灌）：pending-intents / unconsumed-facts / matrix-gaps / budget-check",
        "",
        "## 2 禁注入清单（铁律 2 上下文生命周期受管）",
        "- 13 表 TSV 全量回灌 / 工件原文（artifacts/、*.raw）/ 子代理会话记录",
        "",
        "## 3 幂等续跑判定（重入先查此表）",
    ]
    cl = cache_lines(s, goal_dir)
    if not cl:
        lines.append("- （无 done intent）")
    for iid, st in cl:
        lines.append("- %s  %s" % (iid, st))
    path = os.path.join(goal_dir, "resume-kit.md")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, path)
    print("OK\tresume-kit\tgate=%s\tcached=%d" % (gate, len(cl)))
    return 0
```

dispatch 接 `resume-kit`（--timestamp 可选，缺省取 timeline 最后一行时间戳——确定性）；run_restart 尾部 ⑥ 调用点替换为真调用 `write_resume_kit(goal_dir, ts)`（test_managed_restart 的 happy path 顺带断言 resume-kit.md 出现——在该测试加一行 assertIn）。金样：`python3 cli/tanyin-phases resume-kit --goal-dir tests/fixtures/G-g1 --timestamp=…` 的产物存 `tests/golden/phases-resume-kit.norm`（**注意**：生成命令对 fixture 目录是写操作——禁止直接对 fixtures/ 跑！先 copytree 到 /tmp 再生成再拷回金样文件，与 make_fixtures 纪律一致）。

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_resume_kit tests.test_managed_restart -v`
Expected: 全 PASS

- [ ] **Step 5: 全量回归+提交**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest discover -s tests && python3 tests/run_golden.py`

```bash
git add cli/ledger/phases_engine.py tests/test_resume_kit.py tests/test_managed_restart.py tests/golden/phases-resume-kit.norm
git commit -m "批次3 T7：resume-kit 恢复注入白名单生成器（先对账再干活+禁注入清单+幂等表）+restart⑥接通"
```

---

## Task 8: 幂等续跑判定（tanyin-phases cached，派发前 SKIP/RUN 查询）

**Files:**
- Modify: `cli/ledger/phases_engine.py`（cmd_cached 复用 cache_lines + dispatch 接线）
- Test: `tests/test_idempotent_resume.py`

**Interfaces:**
- Consumes: T7 的 `cache_lines(s, goal_dir)`（单一实现，本任务不重复写）。
- Produces: `tanyin-phases cached --goal-dir D [--intent-id=INT-…]`——设计 §5.2「工件即缓存幂等续跑」的派发侧查询面：全量模式输出 `#count=N` + 每行 `INT-…\tSKIP|RUN`（只列 done intent；--intent-id 单查输出单行 SKIP|RUN，非 done 或不存在=RUN 并附注）。SKILL.md P3 ③派发步与 resume-kit §3 表消费。

- [ ] **Step 1: 写失败测试**（新建 tests/test_idempotent_resume.py）

```python
# -*- coding: utf-8 -*-
"""批次 3 T8：工件即缓存——intent done 且 submission.json 存在→重入跳过。"""
import io, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import core, phases_engine as pe

FIX = os.path.join(HERE, "fixtures", "G-g1")
TAB = chr(9)


class TestCached(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def cached(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pe.dispatch("cached", self.gd, list(args))
        return code, buf.getvalue()

    def test_done_without_file_runs(self):
        code, out = self.cached()
        self.assertEqual(code, 0)
        self.assertIn("#count=1", out)          # 夹具 INT-g1-0001=done
        self.assertIn("INT-g1-0001" + TAB + "RUN", out)   # 无 submission.json → RUN

    def test_done_with_file_skips(self):
        d = os.path.join(self.gd, "submissions", "INT-g1-0001")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "submission.json"), "w", encoding="utf-8").write("{}")
        code, out = self.cached()
        self.assertEqual(code, 0)
        self.assertIn("INT-g1-0001" + TAB + "SKIP", out)

    def test_single_intent_query(self):
        code, out = self.cached("--intent-id=INT-g1-0001")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "RUN")
        code, out = self.cached("--intent-id=INT-g1-0002")   # pending intent
        self.assertEqual(code, 0)
        self.assertIn("RUN", out)

    def test_readonly_no_side_effects(self):
        import hashlib
        before = hashlib.sha256(
            open(os.path.join(self.gd, "timeline.tsv"), "rb").read()).hexdigest()
        self.cached()
        after = hashlib.sha256(
            open(os.path.join(self.gd, "timeline.tsv"), "rb").read()).hexdigest()
        self.assertEqual(before, after)   # 查询面零副作用（§5.3 查询纪律）
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_idempotent_resume -v`
Expected: FAIL（dispatch 不认识 cached）

- [ ] **Step 3: 实现 cmd_cached**（phases_engine.py 追加）

```python
def cmd_cached(goal_dir, rest):
    iid = None
    for tok in rest:
        if tok.startswith("--intent-id="):
            iid = tok.split("=", 1)[1]
        else:
            sys.stderr.write("用法错误: cached [--intent-id=INT-...]\n")
            return 2
    s = core.Session(goal_dir)
    rows = cache_lines(s, goal_dir)
    if iid:
        st = next((v for k, v in rows if k == iid), None)
        print(st if st else "RUN")
        return 0
    print("#count=%d" % len(rows))
    for k, v in rows:
        print(k + chr(9) + v)
    return 0
```

dispatch 接 `cached`。

- [ ] **Step 4: 跑测试+全量回归+提交**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_idempotent_resume -v && python3 -m unittest discover -s tests && python3 tests/run_golden.py`
Expected: 全 PASS

```bash
git add cli/ledger/phases_engine.py tests/test_idempotent_resume.py
git commit -m "批次3 T8：工件即缓存幂等续跑——cached 派发侧查询（done+submission.json→SKIP）"
```

---

## Task 9: SKILL.md 总控路由器本体（常驻权威集 <2K token）

**Files:**
- Create: `SKILL.md`（仓库根=安装树根，契约 12 目录树）
- Test: `tests/test_skill_resident.py`

**Interfaces:**
- Consumes: phases/PROTOCOL.md §2 常驻集清单（八节结构+预算口径）；registry.all_commands()（命令索引一致性单源）。
- Produces: SKILL.md 全文（见 Step 3——即常驻集清单的实例化）；`estimate_tokens(text) -> int`（测试侧 helper，口径随 PROTOCOL.md §2 冻结：CJK 字符数 + ⌈非 CJK 字符数/4⌉）。五宿主 AGENTS.md 系统级注入（§10.2）是批次 6 安装器职责，本任务只交付本体与预算断言。

- [ ] **Step 1: 写失败测试**（新建 tests/test_skill_resident.py）

```python
# -*- coding: utf-8 -*-
"""批次 3 T9/T10：常驻集 <2K token + SKILL 结构 lint + 命令索引一致性 + 九门 md 齐备。"""
import os, re, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import registry

SKILL = os.path.join(ROOT, "SKILL.md")
PHASES = os.path.join(ROOT, "phases")
GATES9 = ("P0", "P1", "P2", "P3", "P4", "P5", "P5.5", "P6.0", "P6")
KNOWN = registry.all_commands() | {
    "tanyin-guard", "tanyin-canary", "tanyin-egress", "tanyin-redact",
    "tanyin-budgetctl", "tanyin-phases", "tanyin-ledger",
    "tanyin-report", "tanyin-viz", "tanyin-replay",
    "ledger-add-edge", "ledger-matrix-freeze",  # SKILL 速查里可能带前缀引用
}


def estimate_tokens(text):
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    other = len(text) - cjk
    return cjk + (other + 3) // 4


class TestSkillResident(unittest.TestCase):
    def test_under_2k_tokens(self):
        with open(SKILL, encoding="utf-8") as f:
            text = f.read()
        t = estimate_tokens(text)
        self.assertLess(t, 2000, "常驻集 %d token 超预算（设计 §11 批次 3 出口）" % t)

    def test_eight_mandatory_sections(self):
        with open(SKILL, encoding="utf-8") as f:
            text = f.read()
        for kw in ("铁律", "九门循环", "P3 演进循环", "命令索引", "恢复协议",
                   "受管重启", "干跑", "路由表"):
            self.assertIn(kw, text, "常驻集缺节: " + kw)
        self.assertNotIn("TODO", text)
        self.assertNotIn("TBD", text)

    def test_command_index_covers_41(self):
        with open(SKILL, encoding="utf-8") as f:
            text = f.read()
        for name in registry.all_commands():
            self.assertIn(name, text, "命令索引缺: " + name)

    def test_referenced_commands_known(self):
        """SKILL.md+phases/*.md 引用命令 ⊆ 已知命令面（§10.3 静态验证①先行）。"""
        files = [SKILL] + [os.path.join(PHASES, n + ".md") for n in GATES9]
        for path in files:
            with open(path, encoding="utf-8") as f:
                text = f.read()
            for m in re.finditer(r"(?:ledger-|tanyin-)([a-z][a-z0-9-]*)", text):
                cand = m.group(0).rstrip("-")
                self.assertIn(cand, KNOWN | registry.all_commands(),
                              "%s 引用未知命令: %s" % (os.path.basename(path), cand))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_skill_resident -v`
Expected: FAIL（SKILL.md 不存在）

- [ ] **Step 3: 写 SKILL.md 全文**（下文即交付本体——预算实测约 1500 token，留 500 余量）

~~~markdown
# 探隐 TanYin · 总控路由器

你是探隐总控：交战区账本的唯一写者。只做四件事——跑命令、派子代理、验收格式、语义推导（产出必须经账本命令落盘）。薄总控五不：不自己写代码、不自己发请求、不自己判重、不自己算哈希、不自己渲染图。凡涉及账本读写而未给出命令的步骤一律不得执行（视为技能缺陷，终止报告）。

## 铁律（违反任何一条=停止并报告）
1. 单写者：子代理/引擎只产 submissions/<intent-id>/submission.json，总控验收后落账。
2. 状态全落盘：不依赖会话记忆；恢复一律走下方恢复协议。
3. 覆盖不可谈判：矩阵空格必须消灭或走 budget-exhausted 披露；九门顺序与出口断言不可跳。
4. 证据即漏洞：无可复现步骤的观察是 fact 不是 finding。
5. CLI 边界：攻击决策/假设生成/漏洞判定禁入 CLI——那是你（LLM）的职责。

## 九门循环（状态机=phases/phases.yaml；断言执法=账本命令）
P0 授权门（八问→add-goal/add-scope/add-cred/add-evidence→append-timeline 落 SKILL 版本→tanyin-egress compile→tanyin-canary deploy）
P1 测绘（侦察子代理→add-asset/add-fact→scope-check 内联）
P2 规划（matrix-init→matrix-freeze 锚点冻结）
P3 演进循环（见下节）
P4 汇总（validate/verify-chain/hash-recheck/matrix-audit→supersede-finding→set-replay-state）
P5 报告（聚合器→ledger-terminal-gate→redact-scan）
P5.5 签发门（人审→approve --verify-signoff）
P6.0 清理门（cleanup-checklist→逆序 revert_cmd）
P6 沉淀（脱敏→tanyin-redact --reverse-verify→approve --knowledge）
每门 duty 详令按需加载 phases/<门>.md；过门唯一方式=tanyin-phases gate --goal-dir <D> --phase <门> --timestamp <T>。

## P3 演进循环（每轮）
⓪ checkpoint+budget-check → ① 扫描（unconsumed-facts/pending-intents/matrix-gaps）→ ② 假设风暴（五路 origin：entity/concept/precedent/adjacency/llm；你只提议，add-intent 算 dedup_key/score；晋升阈值=0.5+0.05*(round-1) 随轮递增；llm 路 quota=5/轮）→ ③ 并行派发（六要素+预算份额；tanyin-budgetctl enforce 前置；tanyin-phases cached 查 SKIP）→ ④ 验收落账（单写者，写前拒收）→ ⑤ 链构建（add-edge attack/cross_ref）→ ⑥ 收敛判定（converge-check：converged|budget-exhausted 皆合法终态）。
事件回边（不离开 P3）：asset-added→add-intent origin=recon-event（直达 pending）+子矩阵行；cred-obtained→add-cred kind=session；scope-amended→amend-scope（须 approvals）→tanyin-egress compile→界外资产复判→canary 复测。

## 命令索引（41 条；签名详见 cli/README.md）
写 19：add-goal add-scope add-intent set-intent-status add-fact add-finding supersede-finding add-asset add-edge add-evidence add-cred set-cred-status amend-scope approve matrix-set matrix-freeze append-timeline budget-log checkpoint
查 11：unconsumed-facts pending-intents matrix-gaps converge-check next-id intent-status matrix-get scope-check budget-check cleanup-checklist redact-scan
校验 10：validate verify-chain hash-recheck matrix-audit state-rebuild set-replay-state ledger-scope-coverage ledger-tree-check ledger-replay-summary ledger-terminal-gate
特殊 1：matrix-init
执行通道：宿主 shell 直通 cli/tanyin-ledger <命令> --goal-dir <D>；配套：tanyin-guard（一切对外命令）、tanyin-budgetctl、tanyin-canary、tanyin-egress、tanyin-phases。

## 恢复协议（先对账再干活）
1. tanyin-ledger verify-chain --goal-dir <D> → FAIL=停+人工（链断不可自愈）。
2. tanyin-ledger state-rebuild --goal-dir <D> → FAIL 则 tanyin-phases rebuild-state --timestamp <T> 对账重建后复跑本条。
3. tanyin-phases resume-kit --goal-dir <D> → 按 resume-kit.md 白名单注入：state.md+本文件+phases/<当前门>.md+四查询摘要（pending-intents/unconsumed-facts/matrix-gaps/budget-check 各一次）。禁注入：13 表全量回灌/工件原文/子代理会话记录。
4. 幂等续跑：intent done 且 submissions/<id>/submission.json 存在→跳过（tanyin-phases cached）。

## 受管重启
上下文用量≥75% 或距上次重启≥10 轮 → tanyin-phases restart --goal-dir <D> --spawn auto --timestamp <T>（护栏：计入预算/10 分钟速率上限/单活跃会话锁）。kill -9/断电兜底：恢复协议走完后 restart --spawn manual 接管。禁止绕过 restart 手工开新会话。

## 干跑模式
无目标自检：P0-P2 照常落账，零对外请求——不 tanyin-guard exec、不 canary probe；egress 只 compile、canary 只 deploy。判定=timeline 无 request: 与 request-ticket 事件。

## 路由表（认知按需加载）
当前门→加载 phases/<门>.md（单门单载，读完即用）；引擎方法论→engines/<引擎>/SKILL.md（批次 4）；知识检索→knowledge/（批次 5）。其余内容一律不进上下文。
~~~

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_skill_resident -v`
Expected: 4 用例 PASS（若 test_referenced_commands_known 因 phases/*.md 未建而找不到文件——本任务先建九个占位会被结构断言拦；正确顺序=本任务先让 SKILL 相关三例绿，referenced 一例依赖 T10，临时用 `@unittest.skipUnless(os.path.isdir(PHASES) and os.path.isfile(os.path.join(PHASES, "P6.0.md")), "T10 未落位")` 门控，T10 落位后自动生效）

- [ ] **Step 5: 提交**

```bash
git add SKILL.md tests/test_skill_resident.py
git commit -m "批次3 T9：SKILL.md 总控路由器——常驻权威集 <2K token（八节结构+命令索引+恢复协议+受管重启+干跑+路由表）"
```

---

## Task 10: phases/P0-P6.md 九门方法论（P3 最厚：风暴五路/资产事件/收敛/重启触发）

**Files:**
- Create: `phases/P0.md`、`phases/P1.md`、`phases/P2.md`、`phases/P3.md`、`phases/P4.md`、`phases/P5.md`、`phases/P5.5.md`、`phases/P6.0.md`、`phases/P6.md`
- Test: `tests/test_skill_resident.py`（追加 TestPhasesMd 类；解除 T9 的 skipUnless 门控）

**Interfaces:**
- Consumes: phases.yaml 各门 duty/events 字符串（内容=其指令化展开）；T3/T6/T7/T8 的四个 tanyin-phases 子命令；41 账本命令。
- Produces: 九门方法论（SKILL 路由表的目标文件）。统一结构头（每门文件必含四段，缺一=结构断言 FAIL）：`## duty（命令序列）`、`## entry 检查单`、`## exit 断言`、`## 回边`。P3.md 额外必含：五路风暴小节、三事件处理器小节、收敛判定小节、受管重启触发小节。

- [ ] **Step 1: 写失败测试**（test_skill_resident.py 追加）

```python
class TestPhasesMd(unittest.TestCase):
    def test_nine_files_exist_with_structure(self):
        for g in GATES9:
            path = os.path.join(PHASES, g + ".md")
            self.assertTrue(os.path.isfile(path), "缺 " + path)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            for sec in ("## duty", "## entry", "## exit", "## 回边"):
                self.assertIn(sec, text, "%s 缺节 %s" % (g, sec))
            self.assertIn("tanyin-phases gate", text, "%s 未声明过门方式" % g)

    def test_p3_md_mandatory_sections(self):
        with open(os.path.join(PHASES, "P3.md"), encoding="utf-8") as f:
            text = f.read()
        for kw in ("entity", "concept", "precedent", "adjacency", "llm",   # 风暴五路
                   "asset-added", "cred-obtained", "scope-amended",       # 三事件
                   "converge-check", "restart",                           # 收敛+重启
                   "recon-event", "submatrix"):
            self.assertIn(kw, text, "P3.md 缺: " + kw)

    def test_yaml_asserts_consistent_with_md(self):
        """P0.md 里出现的断言命令 ⊆ phases.yaml P0.exit.assert 的命令集（声明层单源）。"""
        sys.path.insert(0, os.path.join(ROOT, "cli"))
        from ledger import phases_engine as pe
        data = pe.load_phases()
        for g in GATES9:
            with open(os.path.join(PHASES, g + ".md"), encoding="utf-8") as f:
                text = f.read()
            for a in data["gates"][g]["exit"]["assert"]:
                head = str(a["cmd"]).split()[0].replace("ledger-", "")
                self.assertIn(head, text.replace("ledger-", ""),
                              "%s.md 未提及本门断言命令 %s" % (g, head))
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_skill_resident -v`
Expected: 新增类 FAIL（九门 md 不存在）；T9 的 skipUnless 门控解除后 referenced 一例也须绿。

- [ ] **Step 3: 写九门 md**。P3.md 全文如下（其余八门同构短文：四段结构头+duty 展开=phases.yaml 对应门 duty 字符串的指令化+该门命令清单；P0.md 附八问表落账对照，P4.md 注明 replay-summary 批次 4 前 SKIP 披露义务，P5.md 注明 tanyin-report 批次 6 交付前该门断言将 ENV-HALT）。

~~~markdown
# P3 · 演进循环（方法论指令）

入口：仅经 P2 门进入（gate-exit:P2 在场）。每轮六步，任何写操作只走账本命令。

## duty（每轮命令序列）
⓪ checkpoint --session <本会话> --phase P3 --round <r> --timestamp <T>；budget-check（树形余量，任一维穿=收敛判定走 budget-exhausted 分支）。
① 扫描三查询：unconsumed-facts / pending-intents / matrix-gaps（各一次，计数+top-N）。
② 假设风暴五路（条件触发；你提议、命令判定）：
   - entity 路：新资产/新 fact 派生 → add-intent --origin=entity
   - concept 路：技法页命中 → add-intent --origin=concept --via <技法页引用>
   - precedent 路：先例三元组匹配（批次 5 知识库；本批可空）→ --origin=precedent
   - adjacency 路：邻接攻击面联想 → --origin=adjacency
   - llm 路：自由联想，每轮 quota=5（弱模型档=0）→ --origin=llm
   dedup_key/score 由 add-intent 机械计算（重复键 REJECT=已有同类，不重提）；
   candidate→pending 晋升阈值=0.5+0.05*(round-1)（score 低于阈值=留 candidate，reason 留空）。
③ 并行派发：先 tanyin-budgetctl enforce --intent-id <id>（超份额拒派）；再 tanyin-phases cached --intent-id <id>（SKIP=不派）；派发走六要素委派单（子代理只产 submissions/<intent-id>/submission.json）。
④ 验收落账：按提交 schema 验收，逐条 add-fact/add-finding/add-asset/add-edge/add-cred 落账（单写者；REJECT=打回子代理重写一次）。
⑤ 链构建：add-edge --kind attack / cross_ref（proves/yields 边随 ④ 命令铸）。
⑥ 收敛判定：converge-check → converged 或 budget-exhausted 才可过门（tanyin-phases gate --phase P3）；running=继续下一轮。

## entry 检查单
- gate-exit:P2 在场（verify-chain 跳门检测兜底）
- state.md session=本会话且 active（否则先走恢复协议）

## exit 断言
- tanyin-phases gate --goal-dir <D> --phase P3 --timestamp <T>（断言=ledger-converge-check；budget-exhausted 时门事件自动附 mode=degraded，进 P4 降级流——账本质量不降，P5 首节强制披露未闭合格）

## 回边（不离开 P3 的三事件 + 触发后命令序列）
- asset-added（④ 验收发现新 in_scope 资产）：add-asset 已落 → add-intent --origin=recon-event --kind=recon（直达 pending 不打分）→ 子矩阵行（matrix-set，reason 前缀 submatrix:）→ 计入预算（budgetctl enforce 不豁免测绘）。out_of_scope 资产只记 fact 不 spawn。
- cred-obtained（获得登录态/攻击凭据）：add-cred --kind=session --parent-cred <父>（真值入 vault，secret_ref 占位符）→ authz-diff 候选（批次 4 起触发；本批登记 creds 即止）。
- scope-amended（客户扩授权）：amend-scope --approval <AP-id>（未经审批=账本级 REJECT）→ tanyin-egress compile 重编译 ACL/DNS/OOB → 界外资产复判（scope-check --all-assets）→ 转正资产初始化子矩阵行 → tanyin-canary deploy+probe 复测（干跑模式只 deploy）。

## 受管重启触发（本门独有）
- 自动档：上下文用量≥0.75（restart_context_threshold）或距上次重启≥10 轮（restart_every_n_rounds）→ tanyin-phases restart --spawn auto（护栏：计入预算/速率上限/单活跃会话锁——递归 spawn 会被速率上限与 budget-exhausted 双重掐灭）。
- 兜底档：kill -9/断电后，恢复协议（verify-chain→state-rebuild→resume-kit）走完 → restart --spawn manual（须 state-rebuild PASS 才接管旧锁）。

## 收敛判定语义（终审补全 1）
空格清零（主矩阵+子矩阵）/预算树未穿/无 unconsumed fact/无 blocked intent——四条件全真=converged；预算穿=budget-exhausted（合法终态）。发散由事件链保证（新面不断进入），收敛由锚点+风暴阈值递增保证——收敛是动态平衡。
~~~

- [ ] **Step 4: 跑测试+全量回归**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_skill_resident -v && python3 -m unittest discover -s tests`
Expected: 全 PASS

- [ ] **Step 5: 提交**

```bash
git add phases/P0.md phases/P1.md phases/P2.md phases/P3.md phases/P4.md phases/P5.md phases/P5.5.md phases/P6.0.md phases/P6.md tests/test_skill_resident.py
git commit -m "批次3 T10：九门方法论 md（P3 风暴五路/三资产事件/收敛四条件/受管重启触发；结构头统一）"
```

---
## Task 11: 干跑 eval——P0-P2 零对外请求（批次 3 出口验收①）

**Files:**
- Create: `tests/test_dryrun_p0p2.py`（内含 `dry_run_p0_p2(gd, upto=None)` 驱动函数——总控 P0-P2 行为的确定性脚本化模拟，T12 复用底座）

**Interfaces:**
- Consumes: T3 gate；41 账本命令；tanyin-egress compile（本地产物）；tanyin-canary deploy（本地登记）。PROTOCOL.md §3 干跑口径。
- Produces: `dry_run_p0_p2(goal_dir, upto=None) -> (code, steps_done)`（0=三门全过；2=序列自身用法/环境错即停；upto=断点上限，T12 注入用）。模块级 helpers `ledger(gd, cmd, args)` / `phases(gd, sub, args)`（subprocess 直跑入口，`[sys.executable, 入口]` 范式）。

- [ ] **Step 1: 写测试（含驱动）**（新建 tests/test_dryrun_p0p2.py——驱动是被测物的一部分，本 eval 属「先写全再跑绿」型）

```python
# -*- coding: utf-8 -*-
"""批次 3 T11：干跑 eval——P0-P2 零对外请求（设计 §11 批次 3 出口①；PROTOCOL.md §3 口径）。
dry_run_p0_p2 驱动=总控行为的确定性脚本化：每条命令都与 SKILL.md/九门 md 序列一一对应，
亦是 T12 kill -9 eval 的底座。"""
import os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import core

LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
PHASES_CLI = os.path.join(ROOT, "cli", "tanyin-phases")
EGRESS = os.path.join(ROOT, "cli", "tanyin-egress")
A64 = "a" * 64
TS = "2026-09-24T12:00:00Z"


def ledger(gd, cmd, args=()):
    r = subprocess.run([sys.executable, LEDGER, cmd, "--goal-dir", gd] + list(args),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout, r.stderr


def phases(gd, sub, args=()):
    r = subprocess.run([sys.executable, PHASES_CLI, sub, "--goal-dir", gd] + list(args),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout, r.stderr


def _egress_compile(gd):
    r = subprocess.run([sys.executable, EGRESS, "compile", "--goal-dir", gd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode


STEPS = [
    # --- P0：八问落账（干跑：授权书用本地自建文件占位）---
    ("P0", lambda gd: ledger(gd, "add-goal", [
        "--target=dryrun.example", "--objective=干跑自检",
        "--auth-doc=auth/dry.pdf", "--auth-sha256=" + A64, "--signer=self",
        "--valid-from=2026-09-01", "--valid-until=2026-09-30",
        "--budget=2M;50000;40", "--model-tier=strong", "--guard-tier=T3",
        "--timestamp=" + TS])),
    ("P0", lambda gd: ledger(gd, "add-scope", ["--kind=include",
        "--matcher=*.dryrun.example", "--note=干跑", "--timestamp=" + TS])),
    ("P0", lambda gd: ledger(gd, "add-scope", ["--kind=exclude",
        "--matcher=db.dryrun.example", "--timestamp=" + TS])),
    ("P0", lambda gd: ledger(gd, "add-scope", ["--kind=oob",
        "--matcher=cb.dryrun.example", "--timestamp=" + TS])),
    ("P0", lambda gd: ledger(gd, "append-timeline", ["--actor=总控", "--phase=P0",
        "--event=skill-version sha=dryrun tools.lock=dryrun", "--timestamp=" + TS])),
    ("P0", _egress_compile),                      # 干跑：只 compile（本地产物）
    ("P0", lambda gd: phases(gd, "gate", ["--phase=P0", "--timestamp=" + TS])),
    # --- P1：测绘（干跑：本地虚构资产，不派侦察子代理、零请求）---
    ("P1", lambda gd: ledger(gd, "add-asset", ["--type=root-domain",
        "--value=dryrun.example", "--meta=dry", "--timestamp=" + TS])),
    ("P1", lambda gd: phases(gd, "gate", ["--phase=P1", "--timestamp=" + TS])),
    # --- P2：规划（matrix-freeze 由 gate P2 断言①真跑）---
    ("P2", lambda gd: ledger(gd, "matrix-init", ["--timestamp=" + TS])),
    ("P2", lambda gd: phases(gd, "gate", ["--phase=P2", "--timestamp=" + TS])),
]


def dry_run_p0_p2(gd, upto=None):
    """顺序执行 STEPS；返回 (最后退出码, 已执行步数)。任何步退出 2=序列自身缺陷，即停。"""
    code, done = 0, 0
    for i, (gate, fn) in enumerate(STEPS):
        if upto is not None and i >= upto:
            break
        r = fn(gd)
        code = r[0] if isinstance(r, tuple) else r
        done = i + 1
        if code == 2:
            return 2, done
    return code, done


def fresh_drydir(td, name="G-dryrun"):
    gd = os.path.join(td, name)
    os.makedirs(os.path.join(gd, "auth"), exist_ok=True)
    with open(os.path.join(gd, "auth", "dry.pdf"), "w", encoding="utf-8") as f:
        f.write("dry")
    return gd


class TestDryRun(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = fresh_drydir(self.td)

    def events(self):
        ev = core.TABLES["timeline.tsv"].index("event")
        return [r[ev] for r in core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8)]

    def test_p0_p2_all_gates_zero_egress_requests(self):
        code, done = dry_run_p0_p2(self.gd)
        self.assertEqual(code, 0, "干跑序列第 %d 步退出码 %r" % (done, code))
        evs = self.events()
        self.assertFalse([e for e in evs if e.startswith("request:")],
                         "出现对外请求事件（PROTOCOL.md §3 违规）")
        self.assertFalse([e for e in evs if "request-ticket" in e])
        for g in ("P0", "P1", "P2"):
            self.assertTrue(any(e.startswith("gate-exit:" + g) and "result=PASS" in e
                                for e in evs), "缺 " + g + " 过门事件")
        code, out, _ = ledger(self.gd, "verify-chain")
        self.assertEqual(code, 0, out)
        code, out, _ = ledger(self.gd, "state-rebuild")
        self.assertEqual(code, 0, out)   # state.md absent=合法 PASS

    def test_deterministic_two_runs_same_event_count(self):
        gd2 = fresh_drydir(self.td, "G-dryrun2")
        dry_run_p0_p2(self.gd)
        dry_run_p0_p2(gd2)
        n1 = len(core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8))
        n2 = len(core.read_tsv(os.path.join(gd2, "timeline.tsv"), 8))
        self.assertEqual(n1, n2)   # 同 ts 驱动=同事件数（T12 确定性依赖）


if __name__ == "__main__":
    unittest.main()
```

实现注意（执行者必读，逐条核对后再跑）：
1. `tanyin-egress compile` 的实际子命令/参数以 cli/tanyin-egress 现有 usage 为准（批次 2 交付物，先读文件再对齐——若需 --timestamp 等参数按现状补全；干跑判定只看 timeline 事件面，不检查 egress.acl 内容）。
2. `add-asset` 参数名以 cli/ledger/write_cmds.py `_add_asset` 的 _parse 白名单为准（先读该函数；--meta 若不在白名单则删掉该参）。单 root-domain 资产即可让 tree-check --complete parent 通过（无 parent 边=无断链）；要更真实可加 subdomain+`add-edge --kind=parent --source-id=<子> --target-id=<父>` 两步。
3. P1 gate 断言 `ledger-scope-check --all-assets`：add-asset 落账即内联判定 in_scope（*.dryrun.example ⊆ include 生效链），断言可过。
4. P2 gate 断言② `matrix-gaps --baseline`：matrix-init 默认行键=in_scope assets.value → covered=true 自动成立；断言① matrix-freeze 由 gate runner 作为写类断言真跑（PROTOCOL.md 判定表）。
5. timeline 的 phase 列：add-goal/add-scope 未传 --phase（默认空）——不抬高 reached，跳门检测只认 gate-exit 首现序，三门顺序合法；matrix-init 事件自带 phase=P1（matrix_init.py 硬编码），同样无碍。

- [ ] **Step 2: 跑测试确认通过（按注意 1/2 修正参数后通过）**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_dryrun_p0p2 -v`
Expected: 2 用例 PASS

- [ ] **Step 3: 全量回归+提交**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest discover -s tests && python3 tests/run_golden.py`（全 subprocess 驱动，无平台门控，CI 四格复验）

```bash
git add tests/test_dryrun_p0p2.py
git commit -m "批次3 T11：干跑 eval——P0-P2 零对外请求（三门齐备+request 事件零容忍+确定性底座）"
```

---

## Task 12: kill -9 保真度 eval（批次 3 出口验收②）

**Files:**
- Create: `tests/_kill9_child.py`（断点驱动子进程脚本，10 行）
- Create: `tests/test_kill9_fidelity.py`

**Interfaces:**
- Consumes: T11 的 dry_run_p0_p2/ledger/phases/TS；T5 rebuild-state；T7 resume-kit；T4 checkpoint。
- Produces: 保真度 eval 双层——**层 A（确定性撕裂三态+工件缺失，双平台）**：断点驱动后注入撕裂态，恢复协议后断言 13 表字节指纹不变+state-rebuild PASS+resume-kit 重生成；**层 B（随机断点，仅 POSIX）**：子进程跑到 seed 固定的随机断点，模拟 kill -9 半写丢弃（state.md 删除），恢复后同断言。机制根基=T4 原子写（tmp+os.replace）+T5 对账重建——本 eval 是证据链。

- [ ] **Step 1: 写子进程脚本**（tests/_kill9_child.py）

```python
# -*- coding: utf-8 -*-
"""T12 断点驱动子进程：argv=<goal-dir> <upto>；被父测试进程 subprocess.Popen 启动。"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)   # tests.* 可导入（与 unittest discover 同路径语义）
from tests.test_dryrun_p0p2 import dry_run_p0_p2

code, _ = dry_run_p0_p2(sys.argv[1], upto=int(sys.argv[2]))
sys.exit(0)   # 断点截断不算失败——保真度由父进程的恢复断言判定
```

- [ ] **Step 2: 写测试**（新建 tests/test_kill9_fidelity.py）

```python
# -*- coding: utf-8 -*-
"""批次 3 T12：kill -9 保真度 eval。层 A=确定性撕裂三态（双平台）；层 B=随机断点（POSIX）。"""
import hashlib, os, random, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import core

from tests.test_dryrun_p0p2 import dry_run_p0_p2, ledger, phases, fresh_drydir, TS

CHILD = os.path.join(HERE, "_kill9_child.py")


class TornBase(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.n = 0

    def fresh(self):
        gd = fresh_drydir(self.td, "G-k9-%d" % self.n)
        self.n += 1
        return gd

    def fingerprint(self, gd):
        """13 表字节指纹（恢复不得改变账本——保真度的定义）。"""
        h = hashlib.sha256()
        for t in sorted(core.TABLES):
            p = os.path.join(gd, t)
            h.update(t.encode())
            h.update(open(p, "rb").read() if os.path.exists(p) else b"-")
        return h.hexdigest()

    def drive_with_checkpoint(self, gd, upto=None):
        dry_run_p0_p2(gd, upto=upto)
        ledger(gd, "checkpoint", ["--session=s-k9", "--phase=P3",
                                  "--note=k9", "--timestamp=" + TS])

    def recover_and_assert(self, gd):
        """恢复协议三步（SKILL.md 第⑤节）+保真断言；返回 state-rebuild 输出。"""
        fp_before = self.fingerprint(gd)
        c1, out1, _ = ledger(gd, "verify-chain")
        self.assertEqual(c1, 0, out1)   # 链未断：kill -9 不碰已落盘行（原子追加纪律）
        c2, out2, _ = ledger(gd, "state-rebuild")
        if c2 != 0:
            c3, out3, _ = phases(gd, "rebuild-state", ["--timestamp=" + TS])
            self.assertEqual(c3, 0, out3)
            c2, out2, _ = ledger(gd, "state-rebuild")
        self.assertEqual(c2, 0, out2)
        c4, out4, _ = phases(gd, "resume-kit", ["--timestamp=" + TS])
        self.assertEqual(c4, 0, out4)
        self.assertTrue(os.path.isfile(os.path.join(gd, "resume-kit.md")))
        self.assertEqual(self.fingerprint(gd), fp_before)   # 13 表零变更
        return out2


class TestLayerA_TornStates(TornBase):
    def test_torn_tmp_leftover(self):   # 撕裂态 A：state.md.tmp 残留+state 完整
        gd = self.fresh()
        self.drive_with_checkpoint(gd)
        with open(os.path.join(gd, "state.md.tmp"), "w", encoding="utf-8") as f:
            f.write("torn half")
        c, out, _ = phases(gd, "rebuild-state", ["--timestamp=" + TS])   # rebuild 顺带清扫 tmp
        self.assertEqual(c, 0, out)
        self.assertFalse(os.path.exists(os.path.join(gd, "state.md.tmp")))
        out = self.recover_and_assert(gd)
        self.assertIn("PASS", out)

    def test_torn_state_stale(self):   # 撕裂态 B：timeline 领先 state（checkpoint 撕裂）
        gd = self.fresh()
        self.drive_with_checkpoint(gd)
        ledger(gd, "append-timeline", ["--actor=CLI", "--phase=",
                                       "--event=late-write", "--timestamp=" + TS])
        out = self.recover_and_assert(gd)
        self.assertIn("PASS", out)

    def test_torn_state_missing(self):   # 撕裂态 C：state.md 缺失
        gd = self.fresh()
        self.drive_with_checkpoint(gd)
        os.remove(os.path.join(gd, "state.md"))
        out = self.recover_and_assert(gd)
        self.assertIn("PASS", out)

    def test_torn_resume_kit_missing(self):   # 工件缺失：重生成幂等
        gd = self.fresh()
        self.drive_with_checkpoint(gd)
        p = os.path.join(gd, "resume-kit.md")
        if os.path.exists(p):
            os.remove(p)
        with open(p + ".tmp", "w", encoding="utf-8") as f:
            f.write("torn")
        self.recover_and_assert(gd)   # write_resume_kit 的 tmp+replace 顺带覆盖残tmp
        self.assertFalse(os.path.exists(p + ".tmp"))


@unittest.skipIf(os.name != "posix", "SIGKILL 注入仅 POSIX（CI ubuntu 跑；windows 合法跳过）")
class TestLayerB_RandomKill(TornBase):
    def test_random_breakpoint_recovery(self):
        rng = random.Random(20260924)   # seed 固定：失败可复现
        for trial in range(5):
            gd = self.fresh()
            upto = rng.randint(3, len(STEPS_N) + 1)   # 驱动 12 步+checkpoint
            proc = subprocess.Popen([sys.executable, CHILD, gd, str(upto)],
                                    cwd=ROOT)
            proc.wait(timeout=120)
            # kill -9 半写模拟：已写的 state 摘除（丢弃半写窗口内容）
            sp = os.path.join(gd, "state.md")
            if os.path.isfile(sp) and rng.random() < 0.5:
                os.remove(sp)
            out = self.recover_and_assert(gd)
            self.assertIn("PASS", out, "trial=%d upto=%d" % (trial, upto))


if __name__ == "__main__":
    unittest.main()
```

模块头补一行（与 import 对齐）：`from tests.test_dryrun_p0p2 import STEPS` 并定义 `STEPS_N = len(STEPS)`。

层 B 语义说明（写给评审）：子进程逐条短命 CLI 命令串行，「kill -9 落在命令内 tmp/rename 窗口」的半写态由层 A 三态直接构造证明（tmp 残留/丢弃/缺失——原子写保证无第四态）；层 B 证明「任意断点+state 丢弃后恢复协议闭环」。两层合计=设计出口的 kill -9 保真度 eval。

- [ ] **Step 3: 跑测试确认通过**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest tests.test_kill9_fidelity -v`
Expected: 层 A 4 例+层 B 1 例 PASS（Windows 本地层 B skip=合法）

- [ ] **Step 4: 全量回归+提交**

Run: `cd /Users/wgen/redteam-agent && python3 -m unittest discover -s tests && python3 tests/run_golden.py`

```bash
git add tests/test_kill9_fidelity.py tests/_kill9_child.py
git commit -m "批次3 T12：kill -9 保真度 eval——撕裂三态+POSIX 随机断点（seed 固定），恢复后 13 表零变更+state-rebuild PASS"
```

---

## Task 13: 收口——全量回归+文档+探知项登记+push

**Files:**
- Modify: `cli/README.md`（追加「批次 3」节）
- Create: `docs/design/2026-09-24-b3-discovery-notes.md`（探知项清单落盘=下文「探知项」节全文）
- Modify: `phases/PROTOCOL.md`（仅当实现期与协议有偏差时回写并 bump version=b3-frozen-2+探知项登记；无偏差则不动）

**Interfaces:**
- Consumes: T1-T12 全部交付。
- Produces: 批次 3 出口证据包+对外文档。

- [ ] **Step 1: 全量验证矩阵**

```bash
cd /Users/wgen/redteam-agent
python3 -m unittest discover -s tests -v     # 全部单测（181+新增约 45）
python3 tests/run_golden.py                   # 黄金回归 41 命令（checkpoint 金样已刷新）
python3 cli/tanyin-phases validate            # PASS phases.yaml 契约04合法 asserts=21
```
Expected: 全绿（Windows 侧 CI 复验 py -3 等价入口）。

- [ ] **Step 2: 出口验收逐条实跑打勾**（下节清单，留输出为证）

- [ ] **Step 3: 文档**——cli/README.md 批次 3 节：tanyin-phases 六子命令速查表（validate/gate/restart/resume-kit/cached/rebuild-state，含 --timestamp 确定性说明与 py -3 等价用法）、state.md v2 十键速览、干跑一屏示例；探知项文档落盘。

- [ ] **Step 4: commit + push**

```bash
git add cli/README.md docs/design/2026-09-24-b3-discovery-notes.md
git commit -m "批次3 T13：收口——README 批次3节+探知项清单 G-1..G-11+出口验收证据"
git push
```

---

## 整批出口验收清单（批次 3 Definition of Done）

| # | 验收项（设计 §11 批次 3 行） | 判定命令 | 通过判据 |
|---|---|---|---|
| 1 | 干跑 P0-P2 零对外请求 | `python3 -m unittest tests.test_dryrun_p0p2 -v` | 2 用例 PASS：timeline 无 request:/request-ticket 事件；gate-exit:P0/P1/P2 齐备；verify-chain PASS |
| 2 | kill -9 保真度 eval 通过 | `python3 -m unittest tests.test_kill9_fidelity -v` | 层 A 4 例+层 B 1 例（POSIX；Windows skip 合法）PASS：恢复后 13 表字节指纹不变+state-rebuild PASS+resume-kit 重生成 |
| 3 | token 效率达标（§9.2 首版=告警不 fail；批次 3 硬指标=常驻集） | `python3 -m unittest tests.test_skill_resident -v` | estimate_tokens(SKILL.md) < 2000 |
| 4 | 常驻集 <2K token | 同上 | 同上+八节结构 lint 全过+41 命令索引齐 |
| 5 | 批次 3 两份接口冻结交付 | `python3 cli/tanyin-phases validate && cat phases/PROTOCOL.md` | phases.yaml 合法（gates=9 asserts=21 constants=8 back_edges=3）；PROTOCOL.md version=b3-frozen-1 在场 |
| 6 | phases.yaml 引擎可用 | `python3 cli/tanyin-phases gate --goal-dir <干跑产物> --phase P2 --timestamp <T>` | 退出 0；timeline 增 gate-exit:P2；重复调用 already-passed 幂等 |
| 7 | 受管重启护栏（计入预算/速率上限/单活跃会话） | `python3 -m unittest tests.test_managed_restart -v` | 7 用例 PASS（四护栏各正反例；managed-restart 事件词在场） |
| 8 | 工件即缓存幂等续跑 | `python3 -m unittest tests.test_idempotent_resume -v` | done+submission.json→SKIP；缺件→RUN；查询零副作用 |
| 9 | 既有面不回红 | `python3 -m unittest discover -s tests && python3 tests/run_golden.py` | 181+新增全绿；41 黄金全绿（checkpoint/state-rebuild 金样=有意刷新且 commit 注明） |
| 10 | 双平台 CI | push 后看 .github/workflows/ci.yml | ubuntu+windows × py3.11/3.12 四格全绿 |
| 11 | 探知项上报 | `cat docs/design/2026-09-24-b3-discovery-notes.md` | G-1..G-11 落盘 |

---

## 探知项（接口缺口——计划起草时已发现，执行中继续登记上报）

| # | 缺口 | 影响 | 本计划处置 | 建议裁决 |
|---|---|---|---|---|
| G-1 | **工具面 10→11**：契约 09 冻结「工具箱 10 工具」，phases 引擎需要运行时载体 tanyin-phases（第 11 个） | 契约 09 §3 与实现漂移 | 按新工具推进（铁律 7 类 1 合规：确定性状态机运算，输出金样化）；README 披露 | 契约 09 工具表增补 tanyin-phases（gate/restart 等子命令需要独立运行时载体，并入 selfcheck 面不可行） |
| G-2 | **新资产子矩阵行铸造路径断链**：matrix-set 拒收行外新键（write_cmds:824）、matrix-init 拒收已初始化（matrix_init.py REJECT）——「新资产走子矩阵行」（设计 §5.4 通路①/§4.10）无命令可走 | P3 asset-added 回边的子矩阵初始化无法落账；query_cmds.matrix_gap_cells 已把 submatrix:/authz-diff: 前缀行计入分母（分母在、分子进不去） | 本计划不改 41 面；P3.md 回边写「子矩阵行铸造待 G-2 裁决」 | 裁决 matrix-set 放行 reason 前缀 submatrix: 的新键行（新表面×词表全集），批次 4 前定 |
| G-3 | **重启速率上限常量缺源**：设计载「1 次/N 分钟」未定 N；契约 04 constants 冻结 8 项无此项 | 护栏②参数无契约依据 | 模块常量 RESTART_RATE_MINUTES=10 + --rate-minutes 覆盖（evals 可重放） | 契约 v3 增 restart_rate_minutes 常量 |
| G-4 | **重启计入预算的计量口径**：token_delta 值未载 | 护栏④数额无依据 | 默认 RESTART_TOKEN_COST=2000 + --token-cost 覆盖 | 批次 6 evals 实测基线定标后回写契约 |
| G-5 | **manual 接管的 stale 锁判定**：无跨平台进程存活探测；state-rebuild PASS 只证账本一致不证对方已死 | 双总控并存理论窗口 | manual 须 state-rebuild PASS+timeline 记 takeover-of（留痕可审计）；首发单 session 串行假设下可接受（与 §7.1 graph 多开同款残余） | 批次 6 安装器带 PID/锁文件探测后再收紧 |
| G-6 | **state.md v2 键集**：02a 终审补全 5 授权批次 3 冻结；本计划起草 10 键+handoff | 上游契约需回注 | T4 落位即冻结 | contracts/02a §13 补 state.md v2 键表（引用 phases/PROTOCOL.md） |
| G-7 | **gate-fail 事件词汇**：断言失败事件名契约未载（gate-exit 只该记 PASS） | 引擎输出与跳门检测边界 | 定 gate-fail:<门> assert=<cmd> reason=…（非 gate-exit 前缀，core.GATE_EXIT_EVENT 不误计过门） | 契约 04 事件词汇表补注 |
| G-8 | **干跑的 canary/egress 范围**：P0 duty 含 canary 部署与 egress compile，干跑边界未定义 | 出口①「零对外请求」需可判定 | PROTOCOL.md §3 冻结：egress 只 compile、canary 只 deploy、不 probe | 并入契约 09 tanyin-canary 参数语义注记 |
| G-9 | **风暴阈值过滤的执行位**：candidate→pending 晋升（0.5+0.05*(round-1)）无命令拒收载体（set-intent-status 拒收条件不含阈值） | 弱模型纪律遵循度只能 evals 检测 | SKILL/P3.md 写明公式与纪律；批次 6 evals 增弱模型遵循用例 | 裁决是否给 set-intent-status 增 --round 机械阈值校验（改冻结面需版本化） |
| G-10 | **checkpoint 参数扩展**：--session/--release/--round/--note/--spawn（02a §13 只载 --phase/--event） | 命令签名漂移 | 沿批次 1 探知注记 1 先例（--timestamp 同型追加）；T4 commit 注明 | contracts/02a §13 签名回注 |
| G-11 | **token 估算器口径**：CJK≈1/字+ASCII≈4 字符/token 是跨 tokenizer 近似 | <2K 判定口径 | 测试冻结公式；SKILL.md 预算目标 ≤1600 留 ≥400 余量 | 批次 6 以真实 tokenizer 基线校准系数 |

---

## 执行方式建议

- **主线程亲自**：T1-T3（引擎地基——解析器/校验/gate 协议精度=全系统门禁语义底线）、T4-T5（state.md 是 kill -9 保真度根基）。
- **可并行派发**：T6+T7+T8（T4/T5 接口冻结后三路独立）；T9+T10（SKILL 与九门 md 独立于引擎）；T11+T12（evals，依赖前者齐备）。
- **顺序底线**：每任务出口跑全量回归+黄金不回红才 commit；T13 收口统一 push（中途可随任务 push）。
- 沙盘纪律：只改本计划 Files 节列出的文件；fixtures/ 除两处金样有意刷新外零触碰；绝不写 /Users/wgen/Documents 与 panorama/。

---

## Self-Review 记录（writing-plans 规范自检）

- **Spec 覆盖**：设计 §11 批次 3 行逐项对照——SKILL.md 路由器(T9)/phases.yaml 引擎(T1-T3)/P3 演进循环·风暴五路·资产事件·收敛判定(T10 P3.md+既有查询命令，循环六步的确定性输入全部为既有 11 查询命令)/受管重启·自动+兜底档·护栏(T6)/state.md ≤200 行(T4)/resume-kit 恢复注入白名单(T7)/工件即缓存幂等续跑(T8)；出口三项=干跑(T11)/kill -9(T12)/常驻集<2K(T9)。批次间接口两份→PROTOCOL.md（T3 落盘、T9 实例化）。铁律 7：tanyin-phases 全部子命令=确定性运算、输出金样化；攻击决策/假设生成/漏洞判定全部留在 SKILL.md/P3.md（LLM 职责）。无未覆盖项。
- **占位符扫描**：全文无 TBD/TODO/「稍后实现」；T11/T12 的「实现注意」是防错提示非计划占位（参数名以既有代码白名单为准的核对指令，附了核对目标函数行号）。
- **类型一致**：cache_lines 在 T7 定义、T8 消费同签名；_current_gate 在 T3 定义、T5/T6 消费；state_md.parse_state/write_state/would_overflow 在 T4 定义、T5/T6 消费；gate-exit 事件格式与 fixtures/G-g1 既有行及 core.GATE_EXIT_EVENT 兼容（已对照夹具实文核验）；dry_run_p0_p2 签名 T11 定义、T12 经 _kill9_child.py 消费。
- **夹具事实核对**（起草时实读）：scope.tsv 无 exclude/oob 行（T3 测试先补两行再跑 gate P0）；timeline phase 列自带 P0-P3 门标（T3 keep() 同步抹门标防 reached 抬高误报）；converge-check 恒退出 0、matrix-gaps --baseline covered=false 也退出 0（PROTOCOL 判定表特判两处）；matrix-freeze already-frozen 走 stderr REJECT（判定表幂等容忍条款）；matrix-init 事件 phase 硬编码 P1（T11 注意 5）。
