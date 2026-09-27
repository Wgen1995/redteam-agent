# 批次 7（整改批次）实施计划 —— C1 账本写路径原子化+并发锁/C2 guard exec 硬化/C3 九门权威/C4 tools.lock 信任链/C5 签发四门/High 逐项/战场件/Medium 裁决

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修掉六专家对抗评审 5 Critical（账本写路径非原子/guard exec 绕过/九门伪造快进/tools.lock 信任根=仓内测试钥/报告签发四绕）+ High 逐项 + 靶场首战战场件三件，Medium 逐条裁决收口或登记，全部以「红测=复现专家反例」TDD 落地。

**Architecture:** 不新增命令、不动 13 表 schema（微版本勘误通道）：执法面全部在既有 cli/ledger 单源内收紧——写路径 core.write_tsv/Ctx 全体换 tmp+os.replace（state_md.py:92 先例）+goal 级文件锁；guard 门链前置 argv 归一化与主机变体解码；门事件词进保留字白名单（append-timeline 拒收、run_gate 单源铸造）；tools.lock 信任面隔离+runtime digest 比对；sign_gate 前置授权门+落盘后复扫。

**Tech Stack:** Python 3.11/3.12 标准库（fcntl/msvcrt/hashlib.pbkdf2_hmac/hmac/os.replace/subprocess/multiprocessing）；openssl 子进程验签（既有 supply_chain 单源）；unittest+金样 run_golden 既有机制。

**Spec（三源，执行者必读）:**
- docs/design/2026-09-27-expert-review-consolidated.md —— 六专家台账：5 Critical（全部带文件:行号与复现命令）+High+Medium
- docs/HANDOFF.md「2026-09-27 靶场 LLM 在环首战记录」节 —— 真实 8/20、键失配归因、工具缝四条（terminal-gate 冻结断言等）、技能改进八条
- docs/design/2026-09-21-tanyin-v2-design.md §2 铁律（尤其铁律 5 四层执法/铁律 7 薄 CLI 边界）+§8.5 四层执法语义；§5.2/§5.4 门语义
- 现状基线：748 单测全绿 + 54 金样面 PASS（hash=a347edd7）+ 44 命令面；HEAD=980cff8

## Global Constraints
- 纪律：全部新文件 UTF-8 无 BOM+LF；Windows 入口 `py -3` 等价（.cmd 配对不动）；时间戳显式 `--timestamp=ISO8601` 禁墙钟进账本（egress 运行时日志与 vault nonce 除外，见 T10/T11 裁决）
- 标准库零依赖：不新增 pip 依赖；openssl 仅子进程（验签既有单源 supply_chain.py）
- 金样 54 面零漂移为默认纪律；本计划 T7（信任钥轮换）与 T10（vault 双读过渡）两个任务允许**有意刷新**，刷新面必须单列名单并声明 delta
- 契约面变更（旗标/必填参数）一律微版本勘误（schema_version=2 不递增，文末补记节），T17 统一回注；任何任务不得改 13 表列集与 44 命令名
- 退出码契约冻结 0=通过/1=门禁拒绝/2=用法或环境错误
- 本批红测定义：**红=复现专家复现命令的实测反例**（台账 evidence 列原文），不是泛化单测失败
- panorama/ 与 /Users/wgen/Documents 零触碰
- 每任务 TDD 先红后绿；收尾必跑全套 unittest + run_golden + git status --short 为净

## 背景反例坐标速查（写红测时逐条对照）
| # | 专家复现 | 证据位 | 红测落点 |
|---|---|---|---|
| C1 | write_tsv open(w) 原地截断；SIGKILL 8/8 丢史（200008 行→8KB）；16 并发 add-fact 存活 5 行双 PASS | core.py:52-57；write_cmds.py:241-251 | T1/T2/T3 |
| C2 | rm -r -f / rc=0；http://134744072/（十进制 8.8.8.8）rc=0 | tanyin-guard gate_chain:84-107；enforce.py:39-47,157-213 | T4/T5 |
| C3 | append-timeline 连发 gate-exit:P0..P6 → gate P6 already-passed exit 0 | write_cmds.py:968-985；core.py:110-153 | T6 |
| C4 | fixtures 测试钥重签篡改行 check_lock=0；runtime 不比对 nuclei digest | engines/nuclei/adapter.py:23-46；tests/fixtures/keys/ | T7 |
| C5 | sign 零 approvals 校验；draft 手改直通；goals sha256=deadbeef+过期窗 sign rc=0；脱敏扫描先于落盘 | report_lint.py:228-315/169-224/255-263 | T8/T9 |

## 文件结构图（本批全部触达面）
```
cli/ledger/
  core.py            [T1] write_tsv 原子化；[T6] 保留事件词常量
  filelock.py        [T2 新] goal 级跨平台写锁（fcntl/msvcrt 单源）
  registry.py        [T2] 写命令面接线（锁取自写命令注册表单源）
  write_cmds.py      [T1] Ctx.write_file 原子化；[T6] _append_timeline 保留词拒收
                     [T13] add-fact --no-consume；[T14] matrix-set --batch-file
  enforce.py         [T4] normalize_cmd argv 归一；[T5] _decode_ip_obfuscation 主机变体
  tanyin-guard       [T4/T5] gate_chain 双形比对；[T15] --cred/--action/--timeout；[T10] deploy-vault --secret 退出 argv
  phases_engine.py   [T3] run_restart 孤儿对账；[T12] --usage/--round 必填+阈值消费
  supply_chain.py    [T7] 不动（单源复用）
  engines/nuclei/adapter.py [T7] verify() 增 runtime sha256 比对
  report_lint.py     [T8] _authorization_gate+gates.authorization；[T9] draft 字节比对+pass.json 绑定+落盘后复扫
  vault.py           [T10] nonce+EtM-HMAC+PBKDF2+密钥外移（冻结接口签名不动，双读过渡）
  egress_proxy.py    [T11] decide() oob/canary 判定+build_acl 产 [oob]/[canary] 段+墙钟+轮转+超时
  knowledge.py       [T13] score() 缺基线=ENV 错（exit 2 载体）
  matrix_init.py     [T14] --from-assets 资产类裁剪（默认行为不变）
  check_cmds.py      [T16] terminal-gate 冻结断言改「freeze 时在场行」
tests/
  test_atomic_write_b7.py       [T1 新]
  test_goal_filelock_b7.py      [T2 新]（16 并发 add-fact 存活）
  test_kill9_write_fidelity.py  [T3 新]（200k 行×SIGKILL 8 次+restart 孤儿对账）
  test_guard_argv_norm_b7.py    [T4/T5 新]（专家反例集全录）
  test_gate_authority_b7.py     [T6 新]
  test_tools_trust_face.py      [T7 新]（信任面隔离断言）+engine-nuclei 金样面有意刷新
  test_sign_gates_b7.py         [T8/T9 新]（四绕反例全录）
  test_vault_aead_b7.py         [T10 新]（m1^m2=c1^c2 反例）
  test_egress_oob_canary_b7.py  [T11 新]
  test_restart_threshold_b7.py  [T12 新]
  test_no_consume_k1_b7.py      [T13 新]
  test_matrix_batch_b7.py       [T14 新]
  test_guard_perm_actions_b7.py [T15 新]
  test_scorer_norm_b7.py        [T16 新]（+check_cmds terminal-gate 回归）
  test_b7_medium_closeout.py    [T17 新]（evals vacuous+impact 死分支）
  tests/range/RUNBOOK.md        [T16] GT 键口径显著位新节
  tests/range/ground-truth.json [T16] host_aliases 别名声明位
docs/design/2026-09-27-b7-discovery-notes.md [T17 新]（Medium 裁决表落盘+遗留登记）
docs/HANDOFF.md                  [T17] 流水+状态快照批次 7 行
contracts/（文末补记节）          [T17] 微版本勘误（旗标/必填参数面）
```

## 任务总览（17 任务；每任务独立 TDD 循环+全套回归+commit）
- **T1** 账本写路径原子化：core.write_tsv + Ctx.write_file → tmp+os.replace 单源化（红=半写失败旧内容零损反例）
- **T2** 写命令入口 goal 级文件锁：filelock.py 跨平台单源；写命令注册表全覆盖（台账 18/19 缺失并入）；红=16 并发 add-fact 存活
- **T3** 真 SIGKILL 保真测试+restart 孤儿对账：200k 行 timeline SIGKILL×8（SRE 协议）+三段写孤儿事件对账通道
- **T4** guard argv 规范化：deny-list 双形比对（组合短旗标拆并+长旗标映射）；红=rm -r -f / 反例
- **T5** guard 主机提取硬化：十进制/十六进制/八进制/短式 IPv4 变体解码；红=专家反例集全录
- **T6** 九门权威：append-timeline 保留事件词拒收（gate-exit:/gate-fail）；门事件由 run_gate 单源铸造；红=伪造快进复现
- **T7** tools.lock 信任链：测试钥轮换+信任面隔离断言+adapter runtime nuclei digest 比对
- **T8** 签发四门①授权完整性：auth_doc sha256 比对+窗口门+approvals verify-signoff 强校验；红=deadbeef/过期窗 sign rc=0
- **T9** 签发四门②③④：draft==render_fd 字节比对+pass.json 三工件哈希绑定+落盘后脱敏复扫
- **T10** vault 加密升级：nonce+EtM-HMAC+PBKDF2 KDF+密钥外移+--secret 退出 argv（双读过渡保金样）
- **T11** egress OOB/canary 并入 decide+compile 产 [oob]/[canary] 段+墙钟注入+日志轮转+socket 超时
- **T12** restart 阈值消费：--usage/--round 必填；auto 档 0.75/10 轮阈值执法（单源=phases 默认键）
- **T13** 触发器 no-consume 通道（add-fact --no-consume）+K1 缺基线 exit 2
- **T14** 矩阵批量置格（matrix-set --batch-file，全成全败）+资产类词表裁剪（--from-assets，默认不变）
- **T15** permitted_actions 执法接线：guard --cred/--action account-grant 覆盖门+guard --timeout 通道
- **T16** 战场件：scorer URL 归一化匹配（host 别名）+GT 键口径前置显式化+terminal-gate 冻结断言按 freeze 在场行
- **T17** Medium 裁决收口包（evals vacuous guard+impact 死分支）+裁决表落盘 b7 台账+契约/README 微版本勘误+HANDOFF 记账+push

## Medium 裁决表（T17 落盘到 docs/design/2026-09-27-b7-discovery-notes.md；本表=权威裁决）
| Medium | 裁决 | 去向/判定 |
|---|---|---|
| 退出码塌缩（env 错→1 非 2） | 部分收口 | T10（vault 缺钥=2）/T13（K1 缺基线=2）触达面分型；全仓分型审计登记 v3 |
| supersede 死命令（dup 只能夹具铸） | 遗留 | v3（需新命令面+契约变更）；b7 台账登记 |
| deferred 无出边吸收态 | 遗留 | v3（设计变更：deferred 复活臂）；b7 台账登记 |
| 冻结可追加 frozen_at="" 行 | 收口（裁决+钉死） | T16：追加合法（P3 生长通路 G-2），锚点断言改按 freeze 在场行；测试钉死语义 |
| cred.scope_asset 悬空→图静默丢边 | 遗留 | v3（图查询读侧悬空告警）；b7 台账登记 |
| 端口/服务变更触发器无机检 | 遗留 | v3（TRIGGERS 目录第九类）；b7 台账登记 |
| ④high/critical 死分支（impact 枚举只有高中低） | 收口 | T17：死分支清除或双语归一，grep 判定零残留 |
| evals 空目录 vacuous pass=8 | 收口 | T17：零指标文件=FAIL（vacuous guard）+测试 |
| 等保常量+R11 未审 | 遗留（真人） | 维持批次 6 出口 #17 移交态：R11 人工法务过审，真人载体不变 |
| 真人复核无身份锚 | 遗留 | v3（身份体系超薄 CLI 边界，依赖宿主/组织侧）；b7 台账登记 |
| guard 60s 硬超时 | 收口 | T15：--timeout=秒（默认 60 上限 600）+用法错 exit 2 |
| 重放单报文 | 遗留 | v3（tanyin-replay 多报文/序列重放扩展） |
| 侦察工具未入锁 | 遗留（真人） | 随生产钥仪式（install/KEY-MANAGEMENT 流程）重签 tools.lock 扩键；b7 台账登记 |
| egress now 常量/日志无轮转/无超时 | 收口 | T11：墙钟注入（serve 默认真墙钟，测试显式注入）+5MB×3 轮转+30s socket 超时 |
| 安装只增不删混版 | 遗留 | v3（uninstall/升级面新命令）；b7 台账登记 |

## 出口验收清单（全批完成判定；T17 逐条亲跑并在 HANDOFF 记录）
1. 全套单测：`python3 -m unittest discover -s tests -p "test_*.py" -t .` → OK，计数 = 748+本批新增（T17 记录实际数），零 FAIL 零 ERROR
2. 金样：`python3 tests/run_golden.py` → 54 面 PASS；有意刷新面（T7/T10 名单）之外 hash 前后一致；`git status --short tests/golden` 仅含名单内面
3. C1 原子+锁+保真：`python3 -m unittest tests.test_atomic_write_b7 tests.test_goal_filelock_b7 tests.test_kill9_write_fidelity -v` → 绿；SIGKILL 8/8 后 verify-chain PASS+行数不回滚；16 并发 add-fact 全存活
4. C2 硬化：专家反例集逐条——`guard exec -- rm -r -f /`→REJECT rc=1；`guard exec -- curl http://134744072/`→REJECT host=8.8.8.8；全部反例参数化测试绿
5. C3 权威：`append-timeline --event=gate-exit:P0 …` → REJECT rc=1 零落账；既有干跑 eval（test_dryrun_p0p2）三门 gate-exit PASS 不受扰
6. C4 信任链：信任面隔离断言绿（测试钥签名×生产锚 verify=False）；nuclei 二进制篡改→blocked 提交；`engine-nuclei-adopt` 金样面有意刷新已声明
7. C5 四门：deadbeef 授权书/过期窗口/零 approvals sign → rc=1 gates.authorization FAIL；draft 手改→rc=1；pass.json 篡改→verify rc=1；落盘后复扫绿
8. High 逐项判定：vault m1^m2 关系不成立+篡改 fail-closed；egress compile 含 [oob]/[canary] 且 decide 放行 oob+告警 canary；restart 缺 --usage/--round=exit 2、阈值不足 auto=REJECT；add-fact --no-consume 过 trigger-audit；K1 缺基线=exit 2；matrix-set --batch-file 批量全成全败；guard --action 越权 REJECT
9. 战场件：scorer 别名匹配回归（svc 键×127.0.0.1 GT 键→MATCH）；terminal-gate freeze→matrix-set→PASS 回归绿；RUNBOOK GT 键口径节在盘
10. Medium：裁决表在 b7 台账（15/15 行逐条有裁决）；两个收口件测试绿；遗留项均有去向字段
11. 契约一致性：契约文末补记节含 no-consume/batch-file/--usage/--action 勘误；`python3 -m unittest tests.test_knowledge_contract` 绿（工具面 14 不变）
12. 纪律面：`git status --short` 全净；panorama/ 与 /Users/wgen/Documents 零触碰（`git log --stat` 复核）；UTF-8+LF（`file -I` 抽查新文件）
13. push：`git push origin` 成功，远端 HEAD=本批收口 commit

---

## 任务正文

### Task 1: 账本写路径原子化（core.write_tsv + Ctx.write_file → tmp+os.replace 单源）

**Files:**
- Modify: `cli/ledger/core.py:52-57`（write_tsv）
- Modify: `cli/ledger/write_cmds.py:245-251`（Ctx.write_file）
- Test: `tests/test_atomic_write_b7.py`（新）

**Interfaces:**
- Consumes: `core.write_tsv(path, rows)` / `Ctx.write_file(relpath, text)` 既有签名——全仓调用面零变更，只换实现
- Produces: `core._atomic_write(path, text)` 原子写单源（T3 SIGKILL 保真的机制根基；state_md.py:89-92 同款语义）

- [ ] **Step 1: 写失败测试（半写中断反例=C1 红测）**

```python
# tests/test_atomic_write_b7.py
# -*- coding: utf-8 -*-
"""批次 7 T1：账本写路径原子化（C1）。红=半写中断旧内容零损反例——
现状 core.py:55 open(w) 原地截断：写途中崩溃=旧账本丢失（专家 SIGKILL 8/8 丢史根因）。"""
import os, sys, tempfile, unittest
from unittest import mock
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import core
from ledger.write_cmds import Ctx
from ledger.core import Session

class TestAtomicWrite(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)

    def test_write_tsv_replace_crash_keeps_old_intact(self):
        p = os.path.join(self.d.name, "timeline.tsv")
        core.write_tsv(p, [["a", "b"], ["c", "d"]])
        old = open(p, "rb").read()
        with mock.patch("os.replace", side_effect=OSError(5, "模拟 replace 前夕崩溃")):
            with self.assertRaises(OSError):
                core.write_tsv(p, [["x", "y"]])
        self.assertEqual(open(p, "rb").read(), old, "旧账本零损（原子性定义：要么旧版要么新版）")
        self.assertFalse(os.path.exists(p + ".tmp"), "tmp 残留必须清扫（撕裂态 A 源头）")

    def test_ctx_write_file_replace_crash_keeps_old_intact(self):
        gd = os.path.join(self.d.name, "G-at"); os.makedirs(gd)
        Session(gd)  # 夹具空会话即可（Ctx 只需 dir）
        ctx = Ctx(gd)
        ctx.write_file("attachments/x.txt", "v1")
        p = os.path.join(gd, "attachments", "x.txt")
        old = open(p, "rb").read()
        with mock.patch("os.replace", side_effect=OSError(5, "boom")):
            with self.assertRaises(OSError):
                ctx.write_file("attachments/x.txt", "v2")
        self.assertEqual(open(p, "rb").read(), old)
        self.assertFalse(os.path.exists(p + ".tmp"))

    def test_write_tsv_lf_discipline_unchanged(self):
        p = os.path.join(self.d.name, "t.tsv")
        core.write_tsv(p, [["a", "b"]])
        self.assertNotIn(b"\r", open(p, "rb").read(), "LF 字节纪律不回退")
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_atomic_write_b7 -v`
Expected: 前 2 例 FAIL（`旧账本零损` 断言——现状 open(w) 先截断）或 ERROR；第 3 例 PASS

- [ ] **Step 3: 最小实现**

```python
# cli/ledger/core.py（write_tsv 处；state_md.py:89-92 先例单源化到此）
def _atomic_write(path, text):
    """tmp+fsync+os.replace：kill -9 半写兜底——要么旧版要么新版，无第三态。
    （C1 修复：write_tsv open(w) 原地截断=真实 SIGKILL 静默丢史根因。）"""
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:   # LF 字节纪律
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

def write_tsv(path, rows):
    _atomic_write(path, "".join(chr(9).join(esc(c) for c in r) + chr(10) for r in rows))
```

```python
# cli/ledger/write_cmds.py Ctx.write_file（:245-251 整体替换）
def write_file(self, relpath, text):
    from .core import _atomic_write
    _atomic_write(os.path.join(self.s.dir, relpath), text)
```

- [ ] **Step 4: 跑绿+全套回归**

Run: `python3 -m unittest tests.test_atomic_write_b7 -v` → 3 例 OK；`python3 -m unittest discover -s tests -p "test_*.py" -t .` → 748+3 全绿；`python3 tests/run_golden.py` → 54 面 PASS 零漂移

- [ ] **Step 5: Commit**

```bash
git add cli/ledger/core.py cli/ledger/write_cmds.py tests/test_atomic_write_b7.py
git commit -m "批次7-T1(C1)：账本写路径原子化——core._atomic_write 单源(tmp+fsync+os.replace)+write_tsv/Ctx.write_file 接线；红=半写中断旧内容零损反例（专家 SIGKILL 8/8 丢史根因）"
```

---

### Task 2: goal 级写锁（filelock.py 跨平台单源+写命令注册表全覆盖）

**Files:**
- Create: `cli/ledger/filelock.py`
- Modify: `cli/ledger/registry.py`（命令分发单点接线；先读文件定位分发函数）
- Test: `tests/test_goal_filelock_b7.py`（新）

**Interfaces:**
- Produces: `filelock.goal_lock(goal_dir, timeout=30.0)` contextmanager（fcntl/msvcrt 跨平台）；`registry.WRITE_COMMANDS`（自写命令处理注册表派生的 frozenset 单源，禁手抄名单）
- Consumes: registry.py 现有命令注册/分发结构（Step 0 先 `grep -n "def lookup\|def dispatch\|HANDLERS" cli/ledger/registry.py cli/ledger/write_cmds.py` 定位唯一分发位与写命令注册表）

- [ ] **Step 0: 定位分发单点**

Run: `grep -n "def lookup\|def dispatch\|HANDLERS\|register" cli/ledger/registry.py | head -20`；读 cli/ledger/registry.py 全文（约百余行）。接线点=CLI 分发唯一路径（tanyin-ledger main → registry），锁必须包住「读表→改内存→commit」全程，故在分发处包 goal_lock，不在各 handler 内散装。

- [ ] **Step 1: 写失败测试（16 并发 add-fact 存活=C1 并发半边红测）**

```python
# tests/test_goal_filelock_b7.py
# -*- coding: utf-8 -*-
"""批次 7 T2：写命令并发安全（C1 并发半边）。红=专家 16 并发 add-fact 存活 5 行且双 PASS——
无锁下 Ctx.commit 全表重写=last-writer-wins 丢行。16 个独立子进程（真进程级并发）。"""
import os, subprocess, sys, tempfile, unittest
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import core
# 夹具助手复用既有干跑夹具（fresh_drydir）；add-fact argv 形以 tests/test_write_cmds.py
# 现存 add-fact 用例为准对齐（禁自造参数名）——Step 1 先 grep 对齐：
#   grep -n "add-fact" tests/test_write_cmds.py | head -5
from tests.test_dryrun_p0p2 import fresh_drydir, ledger

class TestGoalLock(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup)

    def test_sixteen_concurrent_add_fact_all_survive(self):
        gd = fresh_drydir(self.td.name, "G-lk")
        def one(i):
            r = subprocess.run(
                [sys.executable, os.path.join(ROOT, "cli", "tanyin-ledger"), "add-fact",
                 "--goal-dir", gd,
                 # ↓ 以下参数键按 test_write_cmds.py 现存用例对齐；timestamp 秒级错开避免同刻拒绝
                 "--timestamp=2026-09-27T00:%02d:00Z" % i],
                capture_output=True, text=True, cwd=ROOT)
            return r.returncode, r.stdout + r.stderr
        with ThreadPoolExecutor(max_workers=16) as ex:
            results = list(ex.map(one, range(16)))
        bad = [(rc, o) for rc, o in results if rc != 0]
        self.assertEqual(bad, [], "16 并发全 rc=0（REJECT/崩溃都算失败）：%s" % bad[:3])
        facts = [l for l in open(os.path.join(gd, "facts.tsv"), encoding="utf-8").read().splitlines() if l.strip()]
        self.assertEqual(len(facts), 16, "16 行一个不能少（专家反例：存活 5 行）")
        c, out, _ = ledger(gd, "verify-chain")
        self.assertEqual(c, 0, out, "并发后链完整（专家反例：双 PASS 假绿）")

    def test_lock_file_not_in_tables(self):
        gd = fresh_drydir(self.td.name, "G-lk2")
        self.assertNotIn(".lock", core.TABLES, "锁文件不进 13 表（fingerprint/金样零干扰）")
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_goal_filelock_b7 -v`
Expected: 并发例 FAIL（行数 < 16 或出现非零 rc——last-writer-wins 丢行）；`.lock` 例 FAIL（常量未建）

- [ ] **Step 3: 最小实现**

```python
# cli/ledger/filelock.py（新）
# -*- coding: utf-8 -*-
"""goal 级写锁（批次 7 T2，C1 并发半边）——跨平台文件锁单源。
锁文件 <goal-dir>/.lock 不进 13 表（core.TABLES 之外：金样/fingerprint/链哈希零干扰）。
POSIX=flock LOCK_EX 阻塞；Windows=msvcrt LK_NBLCK 自旋+超时。超时=OSError，由调用方
按退出码契约翻译为 2（环境/资源类）。"""
import contextlib, os, time

def _lock_nt(fd, timeout):
    import msvcrt
    deadline = time.monotonic() + timeout
    while True:
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.05)

def _unlock_nt(fd):
    import msvcrt
    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)

@contextlib.contextmanager
def goal_lock(goal_dir, timeout=30.0):
    p = os.path.join(goal_dir, ".lock")
    fd = os.open(p, os.O_CREAT | os.O_RDWR)
    try:
        if os.name == "nt":
            _lock_nt(fd, timeout)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            if os.name == "nt":
                _unlock_nt(fd)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(fd)
```

registry.py 分发单点接线（示意；以 Step 0 定位为准）：

```python
# cli/ledger/registry.py 分发处
from .filelock import goal_lock
from . import write_cmds
# 写命令名单=write_cmds 处理注册表键集派生（单源，禁手抄）：
WRITE_COMMANDS = frozenset(write_cmds.COMMANDS)  # 名以实文件为准（write_cmds 的注册表常量名）

def run(name, goal_dir, rest):   # 既有分发函数内，handler 调用外包锁
    if name in WRITE_COMMANDS:
        with goal_lock(goal_dir):
            return _dispatch(name, goal_dir, rest)
    return _dispatch(name, goal_dir, rest)
```

- [ ] **Step 4: 跑绿+全套回归**

Run: `python3 -m unittest tests.test_goal_filelock_b7 -v` → OK；全套 discover 全绿；`python3 tests/run_golden.py` → 54 面 PASS 零漂移（.lock 不进任何表面）

- [ ] **Step 5: Commit**

```bash
git add cli/ledger/filelock.py cli/ledger/registry.py tests/test_goal_filelock_b7.py
git commit -m "批次7-T2(C1)：goal 级文件锁——filelock.py 跨平台单源(fcntl/msvcrt)+registry 写命令分发单点接线(WRITE_COMMANDS 自注册表派生)；红=16 并发 add-fact 存活反例（专家台账 18/19 锁缺失并入）"
```

---

### Task 3: 真 SIGKILL 保真测试（200k 行×8 次）+ restart 三段写孤儿对账

**Files:**
- Create: `tests/test_kill9_write_fidelity.py`
- Modify: `cli/ledger/phases_engine.py:815-938`（run_restart：state 解析前移+孤儿对账步⓪+事件词带 session）
- Test: 同上新文件（POSIX skipUnless；SIGKILL 语义）

**Interfaces:**
- Produces: run_restart 孤儿对账语义——「managed-restart 事件带 session=X 而 state.md session≠X ⇒ checkpoint 未落地（三段写被截断）」⇒ 本次豁免速率窗一次+补记 `managed-restart-orphan prior-session=X` 事件；事件词格式升级 `managed-restart spawn=<s> session=<id>`（`_last_restart_ts` startswith 检测兼容不动）
- Consumes: T1 `_atomic_write`（保真机制根基）；T12 将给 restart 加必填 --usage/--round——本任务测试调用在 T12 落地后随 T12 步骤统一补参

- [ ] **Step 1: 写失败测试（SRE 复现协议红测）**

```python
# tests/test_kill9_write_fidelity.py
# -*- coding: utf-8 -*-
"""批次 7 T3：真实 SIGKILL 保真（SRE 复现协议：200k 行 timeline kill 8 次）+restart 三段写孤儿对账。
红=专家 8/8 静默丢史（200008 行→8KB、verify-chain 假绿 PASS、revision 回滚）。
POSIX-only（SIGKILL 语义）；Windows skip——CI 该文件 skip 不算红（test_kill9 层 B 同款门槛）。"""
import os, random, subprocess, sys, tempfile, time, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)
from ledger import core
from tests.test_dryrun_p0p2 import fresh_drydir, ledger, phases, TS

NCOLS = len(core.TABLES["timeline.tsv"])

def build_big_timeline(gd, n=200008):
    """测试夹具专用：直写大 timeline（链哈希逐行真实，不经 CLI）。"""
    rows, prev = [], core.GENESIS
    for i in range(n):
        ts = "2026-09-27T%02d:%02d:%02dZ" % (i % 24, (i // 24) % 60, i % 60)
        ev = "kill9-fidelity seq=%d" % i
        h = core.row_hash(prev, [ts, "CLI", "P1", ev, "", prev, core.SCHEMA_VERSION])
        rows.append([ts, "CLI", "P1", ev, "", prev, h, core.SCHEMA_VERSION])
        prev = h
    core.write_tsv(os.path.join(gd, "timeline.tsv"), rows)

CHILD = """
import os, sys
sys.path.insert(0, {root}/"cli")
from ledger import core
gd = sys.argv[1]
p = os.path.join(gd, "timeline.tsv")
rows = core.read_tsv(p, len(core.TABLES["timeline.tsv"]))
ts, prev = "2026-09-27T23:59:59Z", rows[-1][6]
wo = [ts, "CLI", "P1", "kill9-append final", "", prev, core.SCHEMA_VERSION]
h = core.row_hash(prev, wo)
rows.append([ts, "CLI", "P1", "kill9-append final", "", prev, h, core.SCHEMA_VERSION])
core.write_tsv(p, rows)
""".format(root=ROOT)

class TestSigkillFidelity(unittest.TestCase):
    @unittest.skipUnless(os.name != "nt", "SIGKILL 语义 POSIX-only")
    def test_200k_rows_survive_eight_sigkills(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        gd = os.path.join(td.name, "G-k9b"); os.makedirs(gd)
        build_big_timeline(gd)
        n0 = len(core.read_tsv(os.path.join(gd, "timeline.tsv"), NCOLS))
        self.assertEqual(n0, 200008)
        rng = random.Random(20270927)   # seed 固定（T12 随机断点先例）
        for k in range(8):
            p = subprocess.Popen([sys.executable, "-c", CHILD, gd])
            time.sleep(rng.uniform(0.002, 0.05))   # 写途中随机断点
            p.kill(); p.wait()
            ok, bad = core.Session(gd).verify_chain()
            self.assertTrue(ok, "第 %d 次 kill 后链断于行 %d（专家反例）" % (k + 1, bad))
            rows = core.read_tsv(os.path.join(gd, "timeline.tsv"), NCOLS)
            self.assertGreaterEqual(len(rows), n0,
                "第 %d 次 kill 后行数回滚（专家反例：200008→8KB、revision 回滚）" % (k + 1))
            self.assertFalse(os.path.exists(os.path.join(gd, "timeline.tsv.tmp")),
                             "第 %d 次 kill 后 tmp 残留（撕裂态 A）" % (k + 1))

class TestRestartOrphanReconcile(unittest.TestCase):
    """SRE High：checkpoint 前注入 kill→孤儿 restart+rate-limit 卡 10min。
    红=孤儿态下再 restart 被 RESTART_RATE_MINUTES=10 拒；绿=孤儿对账放行+补记对账事件。"""
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup)

    def _make_orphan(self, gd):
        # 复刻 run_restart ④⑤（budget-log+managed-restart 事件），跳过 ⑥ checkpoint——
        # 事件词带 session=r-orphan（T3 升级格式），state.md session 保持旧值=孤儿判据
        from ledger import registry, state_md
        registry.lookup("budget-log")(gd, ["--token-delta=2000", "--requests-delta=0",
            "--hours-delta=0", "--dollars-delta=0", "--scope=goal",
            "--note=managed-restart spawn=auto", "--timestamp=2026-09-27T01:00:00Z"])
        from ledger.phases_engine import _append_event
        _append_event(gd, "P1", "managed-restart spawn=auto session=r-orphan", "2026-09-27T01:00:00Z")

    def test_orphan_reconciles_not_rate_blocked(self):
        gd = fresh_drydir(self.td.name, "G-orphan")
        ledger(gd, "checkpoint", ["--session=s-old", "--phase=P1", "--note=old",
                                  "--timestamp=2026-09-27T00:30:00Z"])
        self._make_orphan(gd)
        rc, out, err = phases(gd, "restart", ["--spawn=manual",
                                              "--timestamp=2026-09-27T01:05:00Z"])
        self.assertEqual(rc, 0, "孤儿对账后放行（红现状：rate-limit REJECT 卡 10min）: " + out)
        tl = open(os.path.join(gd, "timeline.tsv"), encoding="utf-8").read()
        self.assertIn("managed-restart-orphan prior-session=r-orphan", tl, "对账事件必须留痕")

    def test_non_orphan_still_rate_limited(self):
        gd = fresh_drydir(self.td.name, "G-rate")
        ledger(gd, "checkpoint", ["--session=s-a", "--phase=P1", "--note=a",
                                  "--timestamp=2026-09-27T00:30:00Z"])
        rc, out, err = phases(gd, "restart", ["--spawn=manual",
                                              "--timestamp=2026-09-27T00:40:00Z"])
        self.assertEqual(rc, 0)
        rc, out, err = phases(gd, "restart", ["--spawn=manual",
                                              "--timestamp=2026-09-27T00:45:00Z"])
        self.assertEqual(rc, 1, "真重启（checkpoint 已落地）仍受速率窗——孤儿豁免不得扩大化")
        self.assertIn("restart-rate-limit", out)
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_kill9_write_fidelity -v`
Expected: SIGKILL 例 FAIL/ERROR（链断或行数回滚或 read_tsv 列数错）；孤儿例 FAIL（rc=1 REJECT restart-rate-limit）；rate 例 PASS

- [ ] **Step 3: 最小实现（run_restart 改造）**

1. state.md 解析块（现 :862-867 ③内）前移到速率检查②之前（孤儿判据需要 fields）。
2. ⑤事件词带 session：`_append_event(goal_dir, gate, "managed-restart spawn=%s session=%s%s" % (spawn, session, takeover), ts)`。
3. 新增孤儿对账步⓪（位于①链检查之后、②速率检查之前）：

```python
# cli/ledger/phases_engine.py run_restart 内（③解析前移后）
# ⓪ 孤儿对账（批次 7 T3，SRE High：checkpoint 前注入 kill→孤儿 restart+rate-limit 卡 10min）：
# 上次 managed-restart 事件带 session=X 而 state.md session≠X=checkpoint 未落地（三段写截断）→
# 豁免本次速率窗一次+补记对账事件（对账留痕）；真重启（session 一致）不受豁免。
last_ts, last_session = _last_restart_event(s)   # _last_restart_ts 改造：同源返回 (ts, session)
if last_session and fields and last_session != fields.get("session"):
    _append_event(goal_dir, _current_gate(s),
                  "managed-restart-orphan prior-session=%s" % last_session, ts)
    last_ts = None   # 豁免本次速率窗
if last_ts:   # 原②速率检查改用 last_ts
    ...（原逻辑不动）
```

`_last_restart_event(s)` 实现（`_last_restart_ts` :804-813 同源改造，旧名保留为薄壳防既有调用面漂移）：

```python
def _last_restart_event(s):
    """最近一次 managed-restart 事件 → (ts, session)；无=None。事件词T3格式：
    managed-restart spawn=<s>[ takeover-of=…][ session=<id>]——session 缺省（旧格式行）返回 ""。"""
    ev_i = core.TABLES["timeline.tsv"].index("event")
    for r in reversed(s.rows("timeline.tsv")):
        if r[ev_i].startswith("managed-restart") and "orphan" not in r[ev_i]:
            sess = ""
            for tok in r[ev_i].split():
                if tok.startswith("session="):
                    sess = tok.split("=", 1)[1]
            return r[0], sess
    return None, None

def _last_restart_ts(s):
    ts, _ = _last_restart_event(s)
    return ts
```

- [ ] **Step 4: 跑绿+全套回归**

Run: `python3 -m unittest tests.test_kill9_write_fidelity tests.test_managed_restart tests.test_idempotent_resume -v` → 全 OK（受管重启既有 10 例零回归）；全套 discover 全绿；`python3 tests/run_golden.py` → 54 面 PASS 零漂移

- [ ] **Step 5: Commit**

```bash
git add tests/test_kill9_write_fidelity.py cli/ledger/phases_engine.py
git commit -m "批次7-T3(C1+SRE)：真 SIGKILL 保真 eval（200k 行×8 次随机断点，链完整+行数不回滚+tmp 零残留）+restart 孤儿写对账（事件词带 session+孤儿豁免速率窗一次+managed-restart-orphan 留痕；真重启速率窗不豁免）"
```

---

### Task 4: guard argv 规范化（deny-list 双形比对：组合短旗标拆并+长旗标映射）

**Files:**
- Modify: `cli/ledger/enforce.py`（新增 `normalize_cmd`/`deny_forms`，DENY_EMBEDDED 同节）
- Modify: `cli/tanyin-guard:84-90`（gate_chain deny 段改双形比对）
- Test: `tests/test_guard_argv_norm_b7.py`（新）

**Interfaces:**
- Produces: `enforce.normalize_cmd(cmd) -> list[str]`（归一形，只作执法比对形，不改写实际执行 argv）；`enforce.deny_forms(cmd) -> list[str]`（比对形全集：原 joined+归一形+sh/bash -c 内嵌 payload 两形）
- Consumes: `DENY_LIST`/`deny_hit` 既有单源（enforce.py:73-80）；tests/test_guard.py 既有夹具助手（Step 0 `grep -n "def \|fresh\|fixture" tests/test_guard.py | head` 对齐夹具形）

- [ ] **Step 1: 写失败测试（红=专家反例 rm -r -f / rc=0）**

```python
# tests/test_guard_argv_norm_b7.py
# -*- coding: utf-8 -*-
"""批次 7 T4：guard exec argv 规范化（C2 反例一）。
红=专家实测 `rm -r -f /` rc=0：deny-list 子串比对只认字面「rm -rf /」，
组合短旗标/长旗标/换序/大小写混写/内嵌 payload 全部逃逸。"""
import os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger.enforce import normalize_cmd, deny_forms
from tests.test_dryrun_p0p2 import fresh_drydir

GUARD = os.path.join(ROOT, "cli", "tanyin-guard")

# 专家复现命令全录（台账 C2 反例一+工程化变体）
REPROS = [
    ["rm", "-r", "-f", "/"],                 # 专家原例
    ["rm", "-f", "-r", "/"],                 # 换序
    ["rm", "--recursive", "--force", "/"],   # 长旗标
    ["rm", "-rF", "/"],                      # 组合+大小写混写
    ["rm", "-r", "-f", "./"],                # ./ 变体
    ["sh", "-c", "rm -r -f /"],              # 内嵌 payload
]

class TestNormalize(unittest.TestCase):
    def test_normalize_joins_flags(self):
        self.assertEqual(normalize_cmd(["rm", "-r", "-f", "/"]), ["rm", "-fr", "/"])
        self.assertEqual(normalize_cmd(["rm", "--recursive", "--force", "/"]), ["rm", "-fr", "/"])
        self.assertEqual(normalize_cmd(["curl", "-s", "-L", "http://x/"]), ["curl", "-ls", "http://x/"])

    def test_deny_forms_embeds_payload(self):
        forms = deny_forms(["sh", "-c", "rm -r -f /"])
        self.assertTrue(any("rm -fr /" in f for f in forms), "归一形必须覆盖内嵌 payload")

class TestGuardReject(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup)

    def test_expert_repros_all_rejected(self):
        gd = fresh_drydir(self.td.name, "G-norm")
        for cmd in REPROS:
            r = subprocess.run([sys.executable, GUARD, "exec", "--goal-dir", gd, "--"] + cmd,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, "REJECT rc=1: %r\n%s%s" % (cmd, r.stdout, r.stderr))
            self.assertIn("deny-list", r.stdout, "拒绝原因=deny-list 命中: %r" % cmd)

    def test_benign_flags_unaffected(self):
        gd = fresh_drydir(self.td.name, "G-norm2")
        r = subprocess.run([sys.executable, GUARD, "exec", "--goal-dir", gd, "--",
                            sys.executable, "-c", "print(1)"], capture_output=True, text=True)
        self.assertNotIn("deny-list", r.stdout, "良性旗标不得误伤")
```

（注：`test_benign_flags_unaffected` 的 argv 以 tanyin-guard 用法 `exec --goal-dir D -- cmd...` 为准；python 可执行名按平台以 `sys.executable` 传入——执行时对齐 test_guard.py 既有调用形。）

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_guard_argv_norm_b7 -v`
Expected: `test_expert_repros_all_rejected` FAIL（rm -r -f / rc=0 无 deny-list 字样）；normalize/forms 例 FAIL（函数未定义）

- [ ] **Step 3: 最小实现**

```python
# cli/ledger/enforce.py（DENY_EMBEDDED 定义后新增）
_LONG2SHORT = {"--recursive": "r", "--force": "f", "--no-preserve-root": "!"}
_SHELL_WRAPPERS = ("sh", "bash", "dash", "zsh")

def normalize_cmd(cmd):
    """argv 归一（批次 7 T4，C2 反例一）：拆组合短旗标→并集重组，供 deny-list 第二形比对。
    「rm -r -f /」「rm -rf /」「rm --recursive --force /」归一为同形 rm -fr /。
    归一只用于执法比对，不改写实际执行的 argv（执法读形，执行原形）。"""
    letters, rest, nopreserve = set(), [], False
    for tok in cmd[1:]:
        if tok in _LONG2SHORT:
            if _LONG2SHORT[tok] == "!":
                nopreserve = True
            else:
                letters.add(_LONG2SHORT[tok])
        elif tok.startswith("-") and not tok.startswith("--") and len(tok) > 1:
            letters.update(tok[1:].lower())
        else:
            rest.append(tok)
    flags = "".join(sorted(letters))
    norm = [cmd[0]] + (["-" + flags] if flags else []) + rest
    if nopreserve:
        norm.append("--no-preserve-root")
    return norm

def deny_forms(cmd):
    """deny-list 比对形全集：原 joined+argv 归一形；shell 包装（sh/bash -c）时
    追加内嵌 payload 的原形+归一形（防「sh -c 'rm -r -f /'」逃逸）。"""
    forms = [" ".join(cmd), " ".join(normalize_cmd(cmd))]
    if cmd and os.path.basename(cmd[0]) in _SHELL_WRAPPERS and "-c" in cmd[1:]:
        i = cmd.index("-c")
        if i + 1 < len(cmd):
            ptoks = cmd[i + 1].split()
            forms.append(cmd[i + 1])
            if ptoks:
                forms.append(" ".join(normalize_cmd(ptoks)))
    return forms
```

```python
# cli/tanyin-guard gate_chain deny 段（:86-90 整体替换）
    from ledger.enforce import deny_forms
    hit = None
    for form in deny_forms(cmd):
        d = deny_hit(form)
        if d:
            hit = d
            break
    if hit:
        print("REJECT" + TAB + "guard" + TAB + "deny-list 命中: " + hit)
        return 1
```

- [ ] **Step 4: 跑绿+全套回归**

Run: `python3 -m unittest tests.test_guard_argv_norm_b7 tests.test_guard tests.test_enforce_unit -v` → 全 OK（guard 既有面零回归）；全套 discover 全绿；金样 54 面 PASS 零漂移

- [ ] **Step 5: Commit**

```bash
git add cli/ledger/enforce.py cli/tanyin-guard tests/test_guard_argv_norm_b7.py
git commit -m "批次7-T4(C2)：guard argv 规范化——normalize_cmd 拆并短旗标+长旗标映射+deny_forms 双形（含 sh -c 内嵌 payload）比对；红=专家反例 rm -r -f / rc=0 全录；良性旗标零误伤对照例在册"
```

---

### Task 5: guard 主机提取硬化（十进制/十六进制/八进制 IPv4 变体解码）

**Files:**
- Modify: `cli/ledger/enforce.py:185-213`（_hosts_of_token 增解码候选；新增 `_decode_ip_obfuscation`）
- Modify: `cli/tanyin-guard`（零改动——extract_hosts 单源自动生效）
- Test: `tests/test_guard_argv_norm_b7.py` 追加类

**Interfaces:**
- Produces: `enforce._decode_ip_obfuscation(hp) -> str`（十进制整数/0x 十六进制/前导 0 八进制 4 段点分 → 规范点分十进制；其余原样）
- 裁决（防误伤）：2-3 段短式（127.1/1.2.3/3.14）**不**解码——与既有 `_looks_host`「排除纯数字版本号」注释同一裁量；解码只认 (a) 无点纯整数 ≤10 位 (b) 恰 4 段全数值点分

- [ ] **Step 1: 写失败测试（红=专家反例 http://134744072/ rc=0）**

```python
# tests/test_guard_argv_norm_b7.py 追加
from ledger.enforce import extract_hosts, _decode_ip_obfuscation

# 专家复现命令全录（台账 C2 反例二+变体）
IP_REPROS = [
    (["curl", "http://134744072/"],  "8.8.8.8"),    # 专家原例：十进制
    (["curl", "http://2130706433/"], "127.0.0.1"),  # 十进制环回
    (["curl", "http://0x7f000001/"], "127.0.0.1"),  # 十六进制
    (["curl", "http://0177.0.0.1/"], "127.0.0.1"),  # 八进制段
    (["curl", "http://0x08080808/"], "8.8.8.8"),    # 十六进制整段
]

class TestHostDeobfuscation(unittest.TestCase):
    def test_unit_decode(self):
        self.assertEqual(_decode_ip_obfuscation("134744072"), "8.8.8.8")
        self.assertEqual(_decode_ip_obfuscation("0x7f000001"), "127.0.0.1")
        self.assertEqual(_decode_ip_obfuscation("0177.0.0.1"), "127.0.0.1")
        self.assertEqual(_decode_ip_obfuscation("example.com"), "example.com", "域名原样")
        self.assertEqual(_decode_ip_obfuscation("3.14"), "3.14", "版本号不解码不误判")
        self.assertEqual(_decode_ip_obfuscation("1.2.3"), "1.2.3", "三段短式不解码")

    def test_extract_hosts_decodes(self):
        self.assertEqual(extract_hosts(["curl", "http://134744072/"]), ["8.8.8.8"])
        self.assertEqual(extract_hosts(["curl", "http://0177.0.0.1/x"]), ["127.0.0.1"])

    def test_guard_rejects_decimal_ip_out_of_scope(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        gd = fresh_drydir(td.name, "G-ip")
        for cmd, host in IP_REPROS:
            r = subprocess.run([sys.executable, GUARD, "exec", "--goal-dir", gd, "--"] + cmd,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, "REJECT: %r\n%s" % (cmd, r.stdout))
            self.assertIn(host, r.stdout, "拒绝消息必须出示解码后主机: %r" % cmd)

    def test_guard_version_number_not_flagged(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        gd = fresh_drydir(td.name, "G-ip2")
        r = subprocess.run([sys.executable, GUARD, "exec", "--goal-dir", gd, "--",
                            sys.executable, "--version=3.14"], capture_output=True, text=True)
        self.assertNotIn("3.14", r.stdout.replace("--version=3.14", ""), "版本号值段不得被当主机拒")
```

（注：`test_guard_rejects_decimal_ip_out_of_scope` 依赖 fresh_drydir 夹具 scope 不含解码后主机——fresh 夹具 scope=P0 三行界内域，8.8.8.8/127.0.0.1 均界外，判定走 `out` 分支 REJECT。）

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_guard_argv_norm_b7.TestHostDeobfuscation -v`
Expected: unit/extract 例 FAIL（函数未定义）；guard 例 FAIL（rc=0 直通——专家反例）

- [ ] **Step 3: 最小实现**

```python
# cli/ledger/enforce.py（_hosts_of_token 前）
def _decode_ip_obfuscation(hp):
    """C2 主机变体解码（批次 7 T5）：十进制整数/0x 十六进制/前导 0 八进制段 →
    规范点分十进制；非变体原样返回。裁决：2-3 段短式不解码（防版本号误判，
    与 _looks_host「排除纯数字版本号」同一裁量）。"""
    def _int(tok):
        try:
            if tok.lower().startswith("0x"):
                return int(tok, 16)
            if len(tok) > 1 and tok.startswith("0") and tok.isdigit():
                return int(tok, 8)
            if tok.isdigit():
                return int(tok)
        except ValueError:
            pass
        return None
    if not hp or ":" in hp:
        return hp
    if "." not in hp:
        n = _int(hp)
        if n is not None and 0 <= n <= 0xFFFFFFFF:
            return "%d.%d.%d.%d" % ((n >> 24) & 255, (n >> 16) & 255, (n >> 8) & 255, n & 255)
        return hp
    parts = hp.split(".")
    if len(parts) == 4:
        ints = [_int(p) for p in parts]
        if all(i is not None for i in ints):
            try:
                return str(ipaddress.IPv4Address(".".join(str(i) for i in ints)))
            except (ipaddress.AddressValueError, ValueError):
                return hp
    return hp
```

```python
# cli/ledger/enforce.py _hosts_of_token 尾段（:197-200 替换为）
        if _looks_host(hp):
            h = hp.lower()
            if h not in out:
                out.append(h)
        dec = _decode_ip_obfuscation(hp)
        if dec != hp and _looks_host(dec):
            d = dec.lower()
            if d not in out:
                out.append(d)
```

- [ ] **Step 4: 跑绿+全套回归**

Run: `python3 -m unittest tests.test_guard_argv_norm_b7 tests.test_guard tests.test_enforce_unit -v` → 全 OK；全套 discover 全绿；金样 54 面 PASS 零漂移

- [ ] **Step 5: Commit**

```bash
git add cli/ledger/enforce.py tests/test_guard_argv_norm_b7.py
git commit -m "批次7-T5(C2)：guard 主机提取硬化——_decode_ip_obfuscation（十进制/0x 十六进制/八进制段→点分十进制）入 extract_hosts 候选集；红=专家反例 http://134744072/（8.8.8.8）逃逸全录；版本号短式不误伤裁决+对照例在册"
```

---

### Task 6: 九门权威（append-timeline 保留事件词拒收；门事件 run_gate 单源铸造）

**Files:**
- Modify: `cli/ledger/core.py:15` 附近（新增 `RESERVED_EVENT_PREFIXES` 常量）
- Modify: `cli/ledger/write_cmds.py:968-985`（_append_timeline 保留词拒收）
- Test: `tests/test_gate_authority_b7.py`（新）

**Interfaces:**
- Produces: `core.RESERVED_EVENT_PREFIXES = ("gate-exit:", "gate-fail")`——门事件唯一铸造路径=`phases_engine.run_gate`（内部 `_append_event` 直写，不经 append-timeline）；T12 的 `managed-restart` 词不进保留表（append-timeline 合法）
- 权威语义（铁律 1 单写者）：timeline 的门事件词域收归引擎单源；append-timeline 保持 actor 自由但事件词受保留表约束

- [ ] **Step 1: 写失败测试（红=专家伪造快进复现）**

```python
# tests/test_gate_authority_b7.py
# -*- coding: utf-8 -*-
"""批次 7 T6：九门权威（C3）。红=专家复现：append-timeline 零白名单，
连发 gate-exit:P0..P6 → gate P6 already-passed exit 0，九门断言零执行即终局。"""
import os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
sys.path.insert(0, os.path.join(HERE, ".."))
from tests.test_dryrun_p0p2 import fresh_drydir, ledger, phases, TS

class TestGateAuthority(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup)

    def test_append_timeline_rejects_gate_exit(self):
        gd = fresh_drydir(self.td.name, "G-ga")
        rc, out, err = ledger(gd, "append-timeline", ["--actor=总控", "--phase=P0",
                                    "--event=gate-exit:P0", "--timestamp=" + TS])
        self.assertEqual(rc, 1, "红现状 rc=0（零白名单）： " + out)
        self.assertIn("REJECT", out)
        tl = open(os.path.join(gd, "timeline.tsv"), encoding="utf-8").read()
        self.assertNotIn("gate-exit:", tl, "REJECT=零落账")

    def test_append_timeline_rejects_gate_fail_and_variant(self):
        gd = fresh_drydir(self.td.name, "G-ga2")
        for ev in ("gate-fail:P0", "gate-exit:P5.5", "gate-exit:P6 asserts=0 result=PASS"):
            rc, out, err = ledger(gd, "append-timeline", ["--actor=总控", "--phase=P0",
                                        "--event=" + ev, "--timestamp=" + TS])
            self.assertEqual(rc, 1, "保留词拒收: " + ev)

    def test_forged_fast_forward_sequence_broken(self):
        """专家复现序列：连发 gate-exit:P0..P6——修复后第一步即断。"""
        gd = fresh_drydir(self.td.name, "G-ga3")
        for g in ("P0", "P1", "P2", "P3", "P4", "P5", "P6"):
            rc, out, err = ledger(gd, "append-timeline", ["--actor=总控", "--phase=" + g,
                                        "--event=gate-exit:" + g, "--timestamp=" + TS])
            self.assertEqual(rc, 1, "第 %s 门伪造被拒: %s" % (g, out))

    def test_legit_gate_mint_unaffected(self):
        """合法铸造路径（tanyin-phases gate P0）照常——白名单只堵 append-timeline 注入侧。"""
        gd = fresh_drydir(self.td.name, "G-ga4")
        rc, out, err = phases(gd, "gate", ["P0", "--timestamp=" + TS])
        self.assertEqual(rc, 0, out + err)
        tl = open(os.path.join(gd, "timeline.tsv"), encoding="utf-8").read()
        self.assertIn("gate-exit:P0", tl, "引擎铸造的门事件在链上")

    def test_managed_restart_word_still_allowed(self):
        gd = fresh_drydir(self.td.name, "G-ga5")
        rc, out, err = ledger(gd, "append-timeline", ["--actor=总控", "--phase=P1",
                                    "--event=managed-restart spawn=auto", "--timestamp=" + TS])
        self.assertEqual(rc, 0, "managed-restart 不进保留表（T6 裁决）: " + out)
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_gate_authority_b7 -v`
Expected: 前四例 FAIL（rc=0 直通——专家反例）；`test_legit_gate_mint_unaffected` PASS（合法路径既有绿）

- [ ] **Step 3: 最小实现**

```python
# cli/ledger/core.py（GATE_EXIT_EVENT :15 之后）
# 门事件词保留表（批次 7 T6，C3 九门权威）：gate-exit:*/gate-fail* 只能由
# phases_engine.run_gate 铸造（单源）；append-timeline 拒收。伪造快进=专家 C3 反例通道。
RESERVED_EVENT_PREFIXES = ("gate-exit:", "gate-fail")
```

```python
# cli/ledger/write_cmds.py _append_timeline（:973 actor 校验后插入）
    if ev.startswith(core.RESERVED_EVENT_PREFIXES):
        raise Reject("保留事件词：门事件只能由 tanyin-phases gate 铸造（append-timeline 拒收）: " + ev)
```

（import 确认：write_cmds.py 已 `from .core import …`； Reject 在同文件既有异常类。）

- [ ] **Step 4: 跑绿+全套回归**

Run: `python3 -m unittest tests.test_gate_authority_b7 tests.test_dryrun_p0p2 tests.test_managed_restart -v` → 全 OK（干跑三门 gate-exit 走合法路径不受扰）；全套 discover 全绿；金样 54 面 PASS 零漂移

- [ ] **Step 5: Commit**

```bash
git add cli/ledger/core.py cli/ledger/write_cmds.py tests/test_gate_authority_b7.py
git commit -m "批次7-T6(C3)：九门权威——RESERVED_EVENT_PREFIXES(gate-exit:/gate-fail)+append-timeline 保留词拒收（REJECT=零落账）；门事件 run_gate 单源铸造不动；红=专家伪造快进序列复现（连发 P0..P6 第一步即断）"
```

---

### Task 7: tools.lock 信任链（测试钥轮换+信任面隔离断言+runtime nuclei digest 比对）

**Files:**
- Rotate: `tests/fixtures/keys/test-signing-key.pem`（新测试钥替换旧钥）+ Create: `tests/fixtures/keys/test-release.pub`（新钥公钥）
- Modify: `engines/nuclei/adapter.py:23-46`（verify() 增 runtime sha256 比对，签名向后兼容）
- Re-sign: 旧钥签发的全部夹具 lock（Step 0 定位；有意刷新名单）
- Test: `tests/test_tools_trust_face.py`（新）

**Interfaces:**
- Produces: `adapter.verify(lock_path, nuclei_path=None) -> (ok, reason)`——第二参缺省 None 时 `shutil.which("nuclei")`；核验顺序=锁验签 → templates.lock → **runtime 二进制 sha256（在场即必比，缺失不比）**；信任面常量：生产锚=`engines/nuclei/release.pub`，测试锚=`tests/fixtures/keys/test-release.pub`
- Consumes: `ledger.supply_chain`（load_lock/sign_entry/verify_entry 单源不动）

**裁决（信任面隔离）：** 专家实证=仓内测试钥能重签过仓内 release.pub 验签 ⇒ 测试钥与生产锚同信任面。本任务生成**全新**测试钥对（与现 release.pub 密码学无关），仓内测试/夹具全走新钥；release.pub 生产锚旋转属生产钥仪式（KEY-MANAGEMENT 人工离线，b6 裁决 C 通道），残留风险登记 b7 台账。

- [ ] **Step 0: 定位旧钥信任面**

Run: `openssl pkey -in tests/fixtures/keys/test-signing-key.pem -pubout | diff - engines/nuclei/release.pub && echo SAME-TRUST-FACE`；`grep -rln "sig" tests/fixtures engines --include="*.lock" | sort`——列出全部待重签 lock 清单（记入本任务 commit message 与金样刷新名单）。

- [ ] **Step 1: 写失败测试（红=信任面隔离断言+runtime digest 反例）**

```python
# tests/test_tools_trust_face.py
# -*- coding: utf-8 -*-
"""批次 7 T7：tools.lock 信任链（C4）。红=专家实证：仓内测试钥重签篡改行 check_lock=0
（测试钥=生产锚同信任面）+runtime 不比对 nuclei 二进制 digest。"""
import hashlib, os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import supply_chain

PROD_PUB = os.path.join(ROOT, "engines", "nuclei", "release.pub")
TEST_KEY = os.path.join(ROOT, "tests", "fixtures", "keys", "test-signing-key.pem")
TEST_PUB = os.path.join(ROOT, "tests", "fixtures", "keys", "test-release.pub")
ADAPTER = os.path.join(ROOT, "engines", "nuclei", "adapter.py")

def _entry():
    return {"key": "nuclei", "version": "t0", "sha256": "ab" * 32, "sig": "", "commit": "c0"}


class TestTrustFace(unittest.TestCase):
    def test_fixture_key_pub_differs_from_prod_anchor(self):
        a = subprocess.run(["openssl", "pkey", "-in", TEST_KEY, "-pubout"],
                           capture_output=True).stdout.strip()
        b = open(PROD_PUB, "rb").read().strip()
        self.assertNotEqual(a, b, "信任面隔离：仓内测试钥公钥≠生产信任锚（专家红：相等）")

    def test_testkey_sig_rejected_by_prod_anchor(self):
        e = _entry()
        supply_chain.sign_entry(e, TEST_KEY)
        ok, why = supply_chain.verify_entry(e, PROD_PUB)
        self.assertFalse(ok, "测试钥签名×生产锚必须失败（红现状：重签过验签）: " + why)

    def test_testkey_sig_accepted_by_test_anchor(self):
        e = _entry()
        supply_chain.sign_entry(e, TEST_KEY)
        ok, why = supply_chain.verify_entry(e, TEST_PUB)
        self.assertTrue(ok, why)


class TestRuntimeDigest(unittest.TestCase):
    def _load_adapter(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("nuc_adapter", ADAPTER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _lock_file(self, td, sha):
        e = _entry()
        e["sha256"] = sha
        supply_chain.sign_entry(e, TEST_KEY)
        lockp = os.path.join(td.name, "tools.lock")
        row = "\t".join([e["key"], e["version"], e["sha256"], e["sig"], e["commit"]])
        open(lockp, "w", encoding="utf-8", newline="\n").write(
            "key\tversion\tsha256\tsig\tcommit\n" + row + "\n")
        return lockp

    def test_tampered_binary_blocked(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        binp = os.path.join(td.name, "nuclei")
        open(binp, "wb").write(b"FAKE-BYTES")   # 在场但不符
        lockp = self._lock_file(td, hashlib.sha256(b"PRISTINE-BYTES").hexdigest())
        ok, why = self._load_adapter().verify(lockp, nuclei_path=binp)
        self.assertFalse(ok, "runtime 二进制 sha256 与 lock 不符必须 blocked（红现状：不比对）")
        self.assertIn("sha256", why)

    def test_pristine_binary_passes_digest(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        binp = os.path.join(td.name, "nuclei")
        open(binp, "wb").write(b"PRISTINE-BYTES")
        lockp = self._lock_file(td, hashlib.sha256(b"PRISTINE-BYTES").hexdigest())
        ok, why = self._load_adapter().verify(lockp, nuclei_path=binp)
        self.assertTrue(ok, why)
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_tools_trust_face -v`
Expected: `test_testkey_sig_rejected_by_prod_anchor` FAIL（红=验证通过）；`test_tampered_binary_blocked` FAIL（红=ok=True 不比对）；其余两例视轮换时点 PASS/FAIL——先跑红如实记录现状

- [ ] **Step 3: 轮换+最小实现**

```bash
# ① 轮换测试钥（与现 release.pub 无信任关系；测试钥可仓内生成，生产钥旋转=离线人工仪式不属本批）
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out tests/fixtures/keys/test-signing-key.pem
openssl pkey -in tests/fixtures/keys/test-signing-key.pem -pubout -out tests/fixtures/keys/test-release.pub
```

② 一次性重签片段（stdin 喂给 python3，不落长期脚本；files=Step 0 清单）：

```python
# 一次性片段（stdin）：逐 lock 以新测试钥重签——签名覆盖=supply_chain.canonical_digest 单源
import sys; sys.path.insert(0, "cli")
from ledger import supply_chain
for path in FILES:   # Step 0 输出的 lock 清单
    lock = supply_chain.load_lock(path)
    for e in lock.values():
        supply_chain.sign_entry(e, "tests/fixtures/keys/test-signing-key.pem")
    # 按原五字段行格式回写（同 T7 测试 _lock_file 的行格式）
```

```python
# engines/nuclei/adapter.py verify()（templates.lock 校验后、return True 前插入）
    # runtime digest（批次 7 T7，C4）：runtime 工件（nuclei 二进制）在场即必比对 lock.sha256。
    # 缺失=不比（canned 离线面行为不变）；在场不符=blocked（信任链延伸到运行时工件）。
    binp = nuclei_path or shutil.which("nuclei")
    if binp and os.path.isfile(binp):
        h = hashlib.sha256(open(binp, "rb").read()).hexdigest()
        if h != lock["nuclei"]["sha256"]:
            return False, "runtime nuclei sha256 与 tools.lock 不符: " + binp
```
（verify 签名改 `def verify(lock_path, nuclei_path=None):`；全部既有调用点零改动兼容。）

- [ ] **Step 4: 跑绿+全套回归**

Run: `python3 -m unittest tests.test_tools_trust_face tests.test_engine_nuclei tests.test_lock_v2 -v` → 全 OK；全套 discover——受旧钥签名影响的夹具面重签后必须全绿；`python3 tests/run_golden.py` → 54 面 PASS，受影响面若字节变化=**有意刷新名单**（commit message 单列 delta）

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/keys/ engines/nuclei/adapter.py tests/test_tools_trust_face.py  # 加 Step 0 重签 lock 清单
git commit -m "批次7-T7(C4)：tools.lock 信任链——测试钥轮换（与生产锚 release.pub 密码学无关）+信任面隔离断言（测试钥签名×生产锚=FAIL）+adapter runtime nuclei sha256 比对（在场即必比，不符=blocked）；夹具 lock 重签名单与金样刷新 delta 见本 message"
```

---

### Task 8: 签发四门①授权完整性（auth_doc sha256+窗口门+approvals verify-signoff 强校验）

**Files:**
- Modify: `cli/ledger/report_lint.py:228-315`（sign_gate：gates 增 `authorization` 键；新增 `_authorization_gate`；cmd_lint 同判定路径自动生效）
- Test: `tests/test_sign_gates_b7.py`（新）

**Interfaces:**
- Produces: gates 新键 `authorization`（FAIL 明细=中文分号串）；判定=①goals.auth_doc 文件 sha256==auth_sha256 ②issuance ts ∈ [valid_from, valid_until] ③approvals.tsv 存在 decision=approved 行——任一不满足=sign/lint rc=1
- Consumes: goals 列名 auth_doc/auth_sha256/signer/valid_from/valid_until（`TABLES["goals.tsv"].index` 单源取下标，禁硬编码列号）；时间解析复用仓内既有 ISO 解析单源（`grep -n "fromisoformat\|def _parse" cli/ledger/report_lint.py cli/ledger/check_cmds.py` 取用，无则本任务内聚一个 `_parse_iso`）

- [ ] **Step 0: 夹具对齐**

Run: `ls tests/ | grep -E "report|sign|lint"`；`grep -rn "sign_gate\|redact_scan" tests/*.py | head`——定位既有 sign/lint 测试的夹具助手与「全绿签发夹具」构造形（T9 复用同一助手；本任务先落一个 `_auth_fixture(gd, sha, vf, vu)` 助手给三例共用）。

- [ ] **Step 1: 写失败测试（红=专家反例 deadbeef/过期窗/零 approvals sign rc=0）**

```python
# tests/test_sign_gates_b7.py
# -*- coding: utf-8 -*-
"""批次 7 T8：签发授权完整性门（C5 反例三）。红=专家实测：goals auth_sha256=deadbeef+
窗口过期+approvals 零校验 → verify-chain PASS、sign rc=0。"""
import hashlib, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
sys.path.insert(0, os.path.join(HERE, ".."))
from ledger import core, report_lint
from tests.test_dryrun_p0p2 import fresh_drydir, ledger, TS

DEAD = "d" * 64
TS_IN_WINDOW = "2026-01-01T12:00:00Z"
TS_AFTER = "2026-09-27T00:00:00Z"

def _sha_of(gd):
    return hashlib.sha256(open(os.path.join(gd, "auth.txt"), "rb").read()).hexdigest()

def _goal_with_auth(gd, sha, vf="2026-01-01T00:00:00Z", vu="2026-01-02T00:00:00Z"):
    """授权书文件+goals 行；argv 键以契约附录 A add-goal 签名为准（执行时对齐既有用例）。"""
    open(os.path.join(gd, "auth.txt"), "wb").write(b"AUTH-DOC-BYTES")
    ledger(gd, "add-goal", [
        "--target=example.com", "--objective=t", "--auth-doc=auth.txt",
        "--auth-sha256=" + sha, "--signer=QA", "--valid-from=" + vf, "--valid-until=" + vu,
        "--rate-limit=10", "--window=1", "--emergency-contact=911", "--budget=1M;10;1",
        "--language=zh", "--timestamp=2026-09-27T00:00:00Z"])


class TestAuthorizationGate(unittest.TestCase):
    def _fresh(self, name):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        return fresh_drydir(td.name, name)

    def test_deadbeef_sha_blocked(self):
        gd = self._fresh("G-auth1")
        _goal_with_auth(gd, sha=DEAD)   # auth.txt 实 sha≠deadbeef
        rc, rep = report_lint.sign_gate(gd, TS_IN_WINDOW, write_credential=True)
        self.assertEqual(rc, 1, "红现状：sign rc=0（零授权校验）")
        self.assertEqual(rep["gates"]["authorization"]["status"], "FAIL")
        self.assertIn("sha256", rep["gates"]["authorization"]["detail"])

    def test_expired_window_blocked(self):
        gd = self._fresh("G-auth2")
        _goal_with_auth(gd, sha=_sha_of(gd))
        rc, rep = report_lint.sign_gate(gd, TS_AFTER, write_credential=True)   # 窗口外签发
        self.assertEqual(rc, 1, "红现状：过期窗 sign rc=0")
        self.assertIn("过期", rep["gates"]["authorization"]["detail"])

    def test_zero_approvals_blocked_and_approved_passes_gate(self):
        gd = self._fresh("G-auth3")
        _goal_with_auth(gd, sha=_sha_of(gd))
        rc, rep = report_lint.sign_gate(gd, TS_IN_WINDOW, write_credential=True)
        self.assertEqual(rc, 1)
        self.assertIn("approvals", rep["gates"]["authorization"]["detail"], "零 approved 行=FAIL")
        # 追加 approved 行后 authorization 门细节消（其余门独立判定不并断言）
        ledger(gd, "approve", ["--decision=approved", "--approver=人工",
                               "--timestamp=2026-01-01T06:00:00Z"])
        rc, rep = report_lint.sign_gate(gd, TS_IN_WINDOW, write_credential=True)
        self.assertNotIn("approvals", rep["gates"]["authorization"]["detail"])

    def test_lint_shares_gate(self):
        gd = self._fresh("G-auth4")
        _goal_with_auth(gd, sha=DEAD)
        rc, out, err = ledger(gd, "lint", ["--goal-dir", gd])   # 入口名以 cli/README 为准
        self.assertEqual(rc, 1, "lint 与 sign 同门（不落凭证路径同样拒收）")
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_sign_gates_b7 -v`
Expected: 授权三例 FAIL（红=rc=0）；lint 例 FAIL；**红态如实录**（若 approve/lint argv 与实面不符，修测试 argv 至真实面再录红——红必须是真反例不是 argv 拼错）

- [ ] **Step 3: 最小实现**

```python
# cli/ledger/report_lint.py（sign_gate 前新增）
def _authorization_gate(goal_dir, s, ts, gates):
    """签发授权完整性（批次 7 T8，C5 反例三）：①授权书 sha256 ②窗口 ③approvals
    verify-signoff。任一不过=gates.authorization FAIL（全门联合 rc 判定不变）。"""
    errs = []
    gi = TABLES["goals.tsv"].index
    rows = s.rows("goals.tsv")
    if not rows:
        errs.append("无 goals 行（授权完整性）")
    else:
        g = rows[0]
        doc, want = g[gi("auth_doc")], (g[gi("auth_sha256")] or "").lower()
        if not doc or not want:
            errs.append("授权书缺：auth_doc/auth_sha256 空（八问表④授权门）")
        else:
            p = doc if os.path.isabs(doc) else os.path.join(goal_dir, doc)
            if not os.path.isfile(p):
                errs.append("授权书文件缺: " + doc)
            else:
                got = hashlib.sha256(open(p, "rb").read()).hexdigest()
                if got != want:
                    errs.append("授权书 sha256 不符 want=%s… got=%s…（deadbeef/手改=FAIL）"
                                % (want[:12], got[:12]))
        t = _parse_iso(ts)
        f, u = _parse_iso(g[gi("valid_from")]), _parse_iso(g[gi("valid_until")])
        if t is not None:
            if f and t < f: errs.append("授权窗口未开始: valid_from=" + g[gi("valid_from")])
            if u and t > u: errs.append("授权窗口已过期: valid_until=" + g[gi("valid_until")])
    ai = TABLES["approvals.tsv"].index
    if not any(r[ai("decision")] == "approved" for r in s.rows("approvals.tsv")):
        errs.append("approvals 无 approved 行（verify-signoff：签发须人工批准在案）")
    if errs:
        gates["authorization"].update(status="FAIL", detail="；".join(errs))
    return not errs

def _parse_iso(z):
    """ISO8601（Z→+00:00）→aware datetime；空/非法=None（窗口判 FAIL 走缺列路径）。"""
    try:
        from datetime import datetime
        return datetime.fromisoformat(z.replace("Z", "+00:00")) if z else None
    except ValueError:
        return None
```

接线：sign_gate gates 字典初值加 `"authorization"`；`ok_all` 判定前调用 `if not _authorization_gate(goal_dir, s, ts, gates): ok_all = False`。确认 cmd_lint 与 sign 共用该聚合（lint 路径同门——Step 1 lint 例验尸）。

- [ ] **Step 4: 跑绿+全套回归**

Run: `python3 -m unittest tests.test_sign_gates_b7 -v` → OK；既有 report/sign 测试全绿（**合法夹具因新门红=夹具授权三件套不全，补夹具不放水**）；全套 discover 全绿；`python3 tests/run_golden.py` → 54 面 PASS（lint/sign 金样面若字节变化=有意刷新名单单列）

- [ ] **Step 5: Commit**

```bash
git add cli/ledger/report_lint.py tests/test_sign_gates_b7.py
git commit -m "批次7-T8(C5①)：签发授权完整性门——_authorization_gate（auth_doc sha256 比对+窗口门+approvals verify-signoff）入 sign/lint 联合判定；红=deadbeef/过期窗/零 approvals sign rc=0 专家反例全录"
```

---

### Task 9: 签发四门②③④（draft==render_fd 字节比对+pass.json 三工件哈希绑定+落盘后脱敏复扫）

**Files:**
- Modify: `cli/ledger/report_lint.py:169-224`（_fd_checks draft 分支改字节比对）
- Modify: `cli/ledger/report_lint.py:255-315`（sign_gate：gates 增 `draft_byte_equal`/`artifact_binding`；redact_scan 移到凭证落盘后复扫+FAIL 删证）
- Test: `tests/test_sign_gates_b7.py` 追加三类

**Interfaces:**
- Produces: ①draft 在场时必与 `report_render.render_fd(goal_dir, fd_id)` 现算输出字节相等（gates.draft_byte_equal）；②pass.json 增 `artifacts: {<相对路径>: sha256}`（draft 文件+E-index active 工件+interim-report 三工件绑定），lint 在场 pass.json 即自动复检绑定（免新旗标，零契约扰动）；③redact-scan 在凭证落盘**之后**对 report/ 全树复扫，FAIL=删凭证+rc=1
- Consumes: T8 的 `_auth_fixture` 全绿签发夹具助手（三工件齐备的会话）；`report_render.render_fd` 既有单源

- [ ] **Step 1: 写失败测试（红=专家反例 draft 手改直通+扫描先于落盘）**

```python
# tests/test_sign_gates_b7.py 追加（复用 T8 夹具助手；FD-id/ts 以夹具实值为准替换占位）
class TestDraftByteEqual(unittest.TestCase):
    def test_hand_edited_draft_blocked(self):
        """专家反例：draft C1→C3 手改直通（现只查 raw 子串在不在）。"""
        gd = <T8 全绿签发夹具助手()>
        draft = os.path.join(gd, "report", "draft", "<FD-id>.md")
        md = open(draft, encoding="utf-8").read()
        open(draft, "w", encoding="utf-8", newline="\n").write(md.replace("C1", "C3", 1))
        rc, rep = report_lint.sign_gate(gd, "<窗口内 ts>", write_credential=False)
        self.assertEqual(rc, 1, "红现状：手改 draft 直通 rc=0")
        self.assertEqual(rep["gates"]["draft_byte_equal"]["status"], "FAIL")


class TestArtifactBinding(unittest.TestCase):
    def test_pass_json_binds_three_artifact_classes(self):
        import json
        gd = <T8 全绿签发夹具助手()>
        rc, rep = report_lint.sign_gate(gd, "<窗口内 ts>", write_credential=True)
        self.assertEqual(rc, 0)
        pj = os.path.join(gd, "report", "signed", "pass.json")
        arts = json.load(open(pj, encoding="utf-8"))["artifacts"]
        self.assertTrue(any(k.startswith("report/draft/") for k in arts), "draft 绑定")
        self.assertTrue(any(not k.startswith("report/") for k in arts), "E-index 工件绑定")
        for k, h in arts.items():
            got = hashlib.sha256(open(os.path.join(gd, k), "rb").read()).hexdigest()
            self.assertEqual(got, h, "绑定即真值: " + k)

    def test_tampered_draft_detected_by_binding(self):
        gd = <T8 全绿签发夹具助手()>   # 先 sign 出 pass.json
        draft = os.path.join(gd, "report", "draft", "<FD-id>.md")
        with open(draft, "a", encoding="utf-8") as f:
            f.write("tampered\n")
        rc, rep = report_lint.cmd_lint(gd, "<窗口内 ts>")   # lint 在场 pass.json 自动复检
        self.assertEqual(rc, 1, "红现状：无绑定复检，签发后篡改不可检")


class TestRescanAfterWrite(unittest.TestCase):
    def test_redact_scan_runs_after_credential_written(self):
        """执法顺序反例（工具缝③）：现扫描先于 pass.json/interim 落盘——终稿不在扫描面。"""
        gd = <T8 全绿签发夹具助手()>
        calls = []
        real = report_lint._subprocess_gate
        def spy(name, argv, gates):
            calls.append((name, os.path.exists(os.path.join(gd, "report", "signed", "pass.json"))))
            return real(name, argv, gates)
        report_lint._subprocess_gate = spy
        try:
            report_lint.sign_gate(gd, "<窗口内 ts>", write_credential=True)
        finally:
            report_lint._subprocess_gate = real
        scan = [c for c in calls if c[0] == "redact_scan"]
        self.assertTrue(scan and scan[-1][1] is True,
                        "红现状：redact_scan 调用时 pass.json 尚未落盘（exists=False）")

    def test_rescan_fail_deletes_credential(self):
        gd = <T8 全绿签发夹具助手()>
        real = report_lint._subprocess_gate
        def fail_redact(name, argv, gates):
            if name == "redact_scan":
                gates["redact_scan"]["status"] = "FAIL"
                return False
            return real(name, argv, gates)
        report_lint._subprocess_gate = fail_redact
        try:
            rc, rep = report_lint.sign_gate(gd, "<窗口内 ts>", write_credential=True)
        finally:
            report_lint._subprocess_gate = real
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(os.path.join(gd, "report", "signed", "pass.json")),
                         "复扫 FAIL=凭证必须删除（fail-closed，不得留半签发态）")
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_sign_gates_b7.TestDraftByteEqual tests.test_sign_gates_b7.TestArtifactBinding tests.test_sign_gates_b7.TestRescanAfterWrite -v`
Expected: 手改例 FAIL（rc=0 直通）；绑定例 FAIL（artifacts 键不存在）；扫描顺序例 FAIL（exists=False）；删证例 FAIL（凭证留存）

- [ ] **Step 3: 最小实现**

```python
# cli/ledger/report_lint.py _fd_checks draft 分支（:169-183 替换）
    if os.path.isfile(draft_path):
        with open(draft_path, encoding="utf-8") as f:
            md = f.read()
        rc, fresh = report_render.render_fd(goal_dir, fd_id)
        if rc != 0 or fresh != md:
            g = gates.setdefault("draft_byte_equal", {"status": "PASS", "detail": ""})
            g["status"] = "FAIL"
            g["detail"] += ("%s: draft 与 render_fd 字节不符（手改=FAIL，批次7 T9）: %s；"
                            % (fd_id, (fresh or "")[:60]))
            ok_all = False
        src = "draft"
    else:
        ...（既有 render 分支原样保留）
```

sign_gate 改造要点（三处，禁止「写两遍」双源）：

```python
    # ②三工件哈希绑定（先 interim 后 pass.json 单次成文）
    arts = {}
    for fd_id in fds:
        p = os.path.join(goal_dir, "report", "draft", fd_id + ".md")
        if os.path.isfile(p):
            arts["report/draft/%s.md" % fd_id] = hashlib.sha256(open(p, "rb").read()).hexdigest()
        for r in report_render._evidence_rows(s, report_render._fd_row(s, fd_id)):
            art = r[TABLES["E-index.tsv"].index("artifact_path")]
            ap = os.path.join(goal_dir, art) if art else ""
            if art and os.path.isfile(ap):
                arts[art.replace(os.sep, "/")] = hashlib.sha256(open(ap, "rb").read()).hexdigest()
    rep = {"goal": ..., "ts": ts, "gates": gates, "artifacts": arts}
    if write_credential:
        signed = os.path.join(goal_dir, "report", "signed")
        os.makedirs(signed, exist_ok=True)
        if terminal == "exhausted":
            ...（interim 先落盘；随后纳入绑定）
            ip = os.path.join(signed, "interim-report.md")
            arts["report/signed/interim-report.md"] = hashlib.sha256(open(ip, "rb").read()).hexdigest()
            rep["artifacts"] = arts   # 同一 dict 引用成文，无第二源
        payload = json.dumps(rep, ensure_ascii=False, sort_keys=True, indent=1) + "\n"
        with open(os.path.join(signed, "pass.json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(payload)
        # ④落盘后复扫（批次 7 T9：扫描面=终稿在场的 report/ 全树）；FAIL=删证 fail-closed
        if not _subprocess_gate("redact_scan",
                                ["redact-scan", "--goal-dir", os.path.abspath(goal_dir),
                                 "--target=" + os.path.abspath(os.path.join(goal_dir, "report"))],
                                gates):
            for fn in ("pass.json", "interim-report.md"):
                fp = os.path.join(signed, fn)
                if os.path.exists(fp):
                    os.unlink(fp)
            return 1, rep
    else:
        # lint 无凭证路径：维持扫描后返回（零产物，顺序语义不受扰）
        if not _subprocess_gate("redact_scan", ["redact-scan", "--goal-dir", os.path.abspath(goal_dir),
            "--target=" + os.path.abspath(os.path.join(goal_dir, "report"))], gates):
            return 1, rep
    # ③绑定复检：goal 内 pass.json 在场即自动复检（lint 入口免新旗标）
    pj = os.path.join(goal_dir, "report", "signed", "pass.json")
    if os.path.isfile(pj):
        import json
        old = json.load(open(pj, encoding="utf-8")).get("artifacts") or {}
        bad = [k for k, h in old.items()
               if not os.path.isfile(os.path.join(goal_dir, k))
               or hashlib.sha256(open(os.path.join(goal_dir, k), "rb").read()).hexdigest() != h]
        if bad:
            g = gates.setdefault("artifact_binding", {"status": "PASS", "detail": ""})
            g["status"] = "FAIL"
            g["detail"] = "绑定失配: " + ", ".join(bad[:5])
            return 1, rep
    return 0, rep
```

- [ ] **Step 4: 跑绿+全套回归**

Run: `python3 -m unittest tests.test_sign_gates_b7 -v` → 全 OK；既有 report/sign 面全绿；全套 discover 全绿；`python3 tests/run_golden.py` → 54 面 PASS（lint 签发面若含 pass.json 字节=有意刷新名单：artifacts 键新增，单列 delta）

- [ ] **Step 5: Commit**

```bash
git add cli/ledger/report_lint.py tests/test_sign_gates_b7.py
git commit -m "批次7-T9(C5②③④)：draft==render_fd 字节比对（手改即 FAIL）+pass.json 三工件 sha256 绑定（lint 在场自动复检）+redact-scan 移到凭证落盘后复扫（FAIL=删证 fail-closed）；红=专家 draft C1→C3 直通与扫描先于落盘反例"
```

---

### Task 10: vault 加密升级（nonce+EtM-HMAC+PBKDF2 KDF+密钥外移+--secret 退出 argv）

**Files:**
- Modify: `cli/ledger/vault.py`（冻结接口 `load_key/secret/secrets/enc_payload/dec_payload` 签名不动，内部升级；`_keystream` 保留为共用原语；新增 `derive_key`）
- Modify: `cli/tanyin-guard:59-83`（cmd_deploy_vault：--secret/--passphrase 退出 argv；stdin/env 通道）
- Test: `tests/test_vault_aead_b7.py`（新）

**Interfaces:**
- Produces: v2 载荷 `b64(MAGIC=b"TV2" + nonce(12B) + ct + tag(HMAC-SHA256 32B))`；子钥派生 `enc_key=sha256(key+":enc")`、`mac_key=sha256(key+":mac")`；keystream 绑定 nonce；`derive_key(passphrase, salt) -> hex`（`hashlib.pbkdf2_hmac` 200k 轮）；`load_key` 优先 `TANYIN_VAULT_KEYFILE` 环境通道（密钥外移），回落 `vault/.key`（兼容）；manifest 算法列 v2=`etm-sha256`
- **裁决（双读过渡）：** dec_payload 无 MAGIC 前缀=legacy XOR 读（stderr 一次性告警）——存量夹具/金样零破坏；全量 cutover（legacy 读退役）登记 b7 台账随生产钥仪式执行

- [ ] **Step 1: 写失败测试（红=专家 m1^m2=c1^c2 实证）**

```python
# tests/test_vault_aead_b7.py
# -*- coding: utf-8 -*-
"""批次 7 T10：vault 加密升级（High：XOR 无 nonce+密钥同盘+密码走 argv）。
红=专家实证：同 key 下 m1^m2==c1^c2（可滚动伪造密文）；篡改无认证；argv 密值。"""
import base64, os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import vault

def b64d(s):
    return base64.b64decode(s)


class TestAead(unittest.TestCase):
    K = "unit-test-key"

    def test_roundtrip(self):
        for pt in ("user\nsecret-123", "中文\n值", ""):
            self.assertEqual(vault.dec_payload(self.K, vault.enc_payload(self.K, pt)), pt)

    def test_xor_malleability_broken(self):
        """红：专家 c1^c2==m1^c2 关系——v2 每载荷独立 nonce，关系不成立。"""
        c1 = b64d(vault.enc_payload(self.K, "aaaa"))
        c2 = b64d(vault.enc_payload(self.K, "bbbb"))
        x = bytes(a ^ b for a, b in zip(c1[3:], c2[3:]))   # 跳过 MAGIC 后本应=可预言关系
        m = bytes(a ^ b for a, b in zip(b"aaaa", b"bbbb"))
        self.assertNotEqual(x[:4], m, "nonce 随机化必须打破 c1^c2=m1^m2（红：相等）")

    def test_same_plaintext_two_ciphertexts(self):
        c1 = vault.enc_payload(self.K, "same")
        c2 = vault.enc_payload(self.K, "same")
        self.assertNotEqual(c1, c2, "nonce 语义：同明文异密文")

    def test_tamper_fail_closed(self):
        raw = bytearray(b64d(vault.enc_payload(self.K, "secret-123")))
        raw[-1] ^= 1
        with self.assertRaises(Exception):
            vault.dec_payload(self.K, base64.b64encode(bytes(raw)).decode())

    def test_legacy_payload_still_readable(self):
        """双读过渡裁决：存量 XOR 夹具可读（迁移未完成前不炸）。"""
        legacy = base64.b64encode(
            bytes(a ^ b for a, b in zip("old-format".encode(), vault._keystream(self.K, 10)))).decode()
        self.assertEqual(vault.dec_payload(self.K, legacy), "old-format")

    def test_derive_key_pbkdf2(self):
        k1 = vault.derive_key("pass-phrase", b"salt-1234")
        k2 = vault.derive_key("pass-phrase", b"salt-5678")
        self.assertEqual(len(k1), 64)
        self.assertNotEqual(k1, k2, "盐异键异")


class TestKeyChannel(unittest.TestCase):
    def test_load_key_prefers_external_keyfile(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        kp = os.path.join(td.name, "external.key")
        open(kp, "w", encoding="utf-8").write("external-key\n")
        gd = os.path.join(td.name, "G-v")
        os.makedirs(os.path.join(gd, "vault"))
        open(os.path.join(gd, "vault", ".key"), "w", encoding="utf-8").write("onsite-key")
        old = os.environ.get("TANYIN_VAULT_KEYFILE")
        os.environ["TANYIN_VAULT_KEYFILE"] = kp
        try:
            self.assertEqual(vault.load_key(gd), "external-key", "外移密钥优先（密钥同盘 High）")
        finally:
            if old is None:
                os.environ.pop("TANYIN_VAULT_KEYFILE", None)
            else:
                os.environ["TANYIN_VAULT_KEYFILE"] = old

    def test_deploy_vault_rejects_secret_in_argv(self):
        """红：密码/密值走 argv（进程列表可读）——改 stdin/env 通道后 argv 形=usage exit 2。"""
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        gd = os.path.join(td.name, "G-dv")
        os.makedirs(gd)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-guard"),
                            "deploy-vault", "--goal-dir", gd,
                            "--cred=1", "--username=u", "--secret=topsecret"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, "红现状：--secret argv 被接受")
        self.assertNotIn("topsecret", r.stdout + r.stderr, "密值不得回显")
        # env 通道成功部署
        env = dict(os.environ, TANYIN_VAULT_SECRET="topsecret", TANYIN_VAULT_PASSPHRASE="pp")
        r2 = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-guard"),
                             "deploy-vault", "--goal-dir", gd, "--cred=1", "--username=u"],
                            capture_output=True, text=True, env=env)
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        mf = open(os.path.join(gd, "vault", "manifest.tsv"), encoding="utf-8").read()
        self.assertIn("etm-sha256", mf, "v2 算法列")
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_vault_aead_b7 -v`
Expected: malleability/双密文/篡改例 FAIL（现状 XOR 无认证无 nonce）；argv 例 FAIL（rc=0）；外移例 FAIL（env 未消费）

- [ ] **Step 3: 最小实现**

```python
# cli/ledger/vault.py（冻结区之外的实现升级；接口签名不动）
MAGIC = b"TV2"
import hmac as _hmac

def _subkeys(key):
    return (hashlib.sha256((key + ":enc").encode()).digest(),
            hashlib.sha256((key + ":mac").encode()).digest())

def enc_payload(key, plaintext):
    """v2（批次 7 T10）：nonce 随机化+EtM(HMAC-SHA256)——m1^m2=c1^c2 关系消除、
    篡改 fail-closed。签名不变：enc_payload(key, plaintext) -> b64 str。"""
    data = plaintext.encode("utf-8")
    enc_key, mac_key = _subkeys(key)
    nonce = os.urandom(12)
    ks = _keystream(enc_key.hex() + ":" + nonce.hex(), len(data))
    ct = bytes(a ^ b for a, b in zip(data, ks))
    tag = _hmac.new(mac_key, nonce + ct, hashlib.sha256).digest()
    return base64.b64encode(MAGIC + nonce + ct + tag).decode()

def dec_payload(key, b64):
    raw = base64.b64decode(b64)
    if not raw.startswith(MAGIC):
        sys.stderr.write("vault legacy XOR 载荷（无认证）——请重部署升级 v2\n")   # 双读过渡裁决
        data = bytes(a ^ b for a, b in zip(raw, _keystream(key, len(raw))))
        return data.decode("utf-8")
    enc_key, mac_key = _subkeys(key)
    nonce, ct, tag = raw[3:15], raw[15:-32], raw[-32:]
    want = _hmac.new(mac_key, nonce + ct, hashlib.sha256).digest()
    if not _hmac.compare_digest(tag, want):
        raise ValueError("vault 载荷认证失败（篡改=拒绝，fail-closed）")
    ks = _keystream(enc_key.hex() + ":" + nonce.hex(), len(ct))
    return bytes(a ^ b for a, b in zip(ct, ks)).decode("utf-8")

def derive_key(passphrase, salt):
    """PBKDF2-HMAC-SHA256（stdlib 单源；200k 轮）——passphrase→主钥，防弱口令直用。"""
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 200_000).hex()

def load_key(gd):
    # 密钥外移（批次 7 T10）：env 通道优先；回落 vault/.key（存量兼容）
    p = os.environ.get("TANYIN_VAULT_KEYFILE") or os.path.join(vault_dir(gd), ".key")
    return open(p, encoding="utf-8").read().strip() if os.path.isfile(p) else None
```
（`import sys` 补进 vault.py 头部；deploy-vault 侧： passphrase 经 PBKDF2+`vault/.salt`(16B os.urandom)→主钥写 .key；secret 从 env/stdin 读，--secret= 在 argv 出现即 usage exit 2；manifest 算法列写 etm-sha256。）

- [ ] **Step 4: 跑绿+全套回归**

Run: `python3 -m unittest tests.test_vault_aead_b7 tests.test_guard -v` → 全 OK；全套 discover 全绿（replay/guard 真值回注面走 vault.secret 单源自动生效）；`python3 tests/run_golden.py` → 54 面 PASS——deploy-vault 输出面（manifest sha 段）若在金样=**有意刷新名单**（nonce 语义必然逐次不同，该面必须改断言形状或移出金样，禁真值入金样）

- [ ] **Step 5: Commit**

```bash
git add cli/ledger/vault.py cli/tanyin-guard tests/test_vault_aead_b7.py
git commit -m "批次7-T10(High)：vault v2——nonce 随机化+EtM-HMAC（m1^m2=c1^c2 关系消除/篡改 fail-closed）+PBKDF2 密钥派生+密钥外移(env TANYIN_VAULT_KEYFILE)+--secret 退出 argv(stdin/env 通道)；双读过渡保金样，legacy 退役登记台账"
```

---

### Task 11: egress OOB/canary 并入 decide+compile 产 [oob]/[canary] 段+墙钟+轮转+超时

**Files:**
- Modify: `cli/ledger/egress_proxy.py`（decide:119；build_acl:42-78；serve/serve_text:304-309；log 行；handler timeout）
- Test: `tests/test_egress_oob_canary_b7.py`（新）

**Interfaces:**
- Produces: `decide(acl, host, port) -> (verdict, reason)`，verdict ∈ {"allow","deny","oob","canary"}——canary 命中=**告警放行**（探测点语义：阻断反而掩盖触达事实）、oob=白名单放行、allow 集放行、其余默认拒；`build_acl` 产 `[oob]`（scope kind=oob 行）与 `[canary]`（scope kind=canary 行+canary/recon-decoys.tsv 部署诱饵）段；serve 日志行真墙钟（`now=None` 缺省→UTC ISO 墙钟；测试显式注入固定 now）；日志轮转 5MB×保留 3 代（`egress.log.1..3`）；handler socket 超时 30s

- [ ] **Step 0: 读面定位**

Run: `grep -n "def \|log_line\|timeout" cli/ledger/egress_proxy.py`——以实文件函数名为准（骨架中 load_acl/_wild_hit 为示意名，执行时对齐既有名）；既有 test_egress_proxy.py 的 now 注入用法一并对齐（固定 now 通道保留=测试确定性不回退）。

- [ ] **Step 1: 写失败测试（红=专家 OOB/canary 默认失效）**

```python
# tests/test_egress_oob_canary_b7.py
# -*- coding: utf-8 -*-
"""批次 7 T11：egress OOB/canary 接线（High：decide() 只查 allow 集、compile 不产
[canary] 段——两声明面默认失效）+墙钟注入+日志轮转+socket 超时。"""
import os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import egress_proxy as ep

# 名对齐 Step 0：骨架用 ep.load_acl/ep.build_acl/ep.decide，实文件为准

class TestDecide(unittest.TestCase):
    def _acl(self, text):
        return ep.load_acl(text)

    def test_oob_classified_allow(self):
        acl = self._acl("[acl]\nallow in.example\n[oob]\noob.example\n")
        v, why = ep.decide(acl, "oob.example", 443)
        self.assertEqual(v, "oob", "红现状：只查 allow 集→oob 落默认拒")

    def test_canary_classified_allow(self):
        acl = self._acl("[acl]\nallow in.example\n[canary]\ncan.example\n")
        v, why = ep.decide(acl, "can.example", 80)
        self.assertEqual(v, "canary", "canary 命中=告警类放行（探测点）")

    def test_default_deny_unchanged(self):
        acl = self._acl("[acl]\nallow in.example\n")
        v, why = ep.decide(acl, "evil.example", 443)
        self.assertEqual(v, "deny")


class TestCompile(unittest.TestCase):
    def test_compile_emits_oob_and_canary_sections(self):
        import subprocess
        ROOT = os.path.join(HERE, "..")
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        gd = os.path.join(td.name, "G-eg")
        os.makedirs(gd)
        # scope kind=oob 行（argv 以契约附录 A add-scope 为准）
        r = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-ledger"),
                            "add-scope", "--goal-dir", gd, "--kind=oob",
                            "--matcher=oob.example", "--timestamp=2026-09-27T00:00:00Z"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        os.makedirs(os.path.join(gd, "canary"))
        open(os.path.join(gd, "canary", "recon-decoys.tsv"), "w", encoding="utf-8").write(
            "host\tcan-decoy.example\n")
        out = os.path.join(td.name, "egress.acl")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "cli", "tanyin-egress"),
                            "compile", "--goal-dir", gd, "--out", out],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        acl = open(out, encoding="utf-8").read()
        self.assertIn("[oob]", acl) and self.assertIn("oob.example", acl)
        self.assertIn("[canary]", acl, "红现状：compile v2 不产 canary 段（注释自认）")
        self.assertIn("can-decoy.example", acl)


class TestLogOps(unittest.TestCase):
    def test_wall_clock_default_not_constant(self):
        import re
        line = ep.format_log_line(None, "allow", "h.example", 443, "in")   # now=None→真墙钟
        self.assertTrue(re.match(r"^\d{4}-\d{2}-\d{2}T", line), "缺省=真墙钟（红：EPOCH 常量）")
        line2 = ep.format_log_line("2026-09-27T00:00:00Z", "allow", "h.example", 443, "in")
        self.assertTrue(line2.startswith("2026-09-27T00:00:00Z"), "显式注入固定 now=测试确定性")

    def test_log_rotation(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        p = os.path.join(td.name, "egress.log")
        open(p, "w").write("x" * (ep.MAX_LOG_BYTES + 1))
        ep.append_log_line(p, "2026-09-27T00:00:00Z allow h 443 in")
        self.assertTrue(os.path.isfile(p + ".1"), "超限轮转 .1 代")
        self.assertLess(os.path.getsize(p), ep.MAX_LOG_BYTES)
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_egress_oob_canary_b7 -v`
Expected: decide 两例 FAIL（deny/非常量）；compile 例 FAIL（无 [canary]）；墙钟例 FAIL（EPOCH 常量）；轮转 FAIL（函数缺位）

- [ ] **Step 3: 最小实现**

```python
# cli/ledger/egress_proxy.py
MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_KEEP = 3
HANDLER_TIMEOUT_S = 30

def decide(acl, host, port):
    """判定（批次 7 T11，High）：canary 命中=告警放行（探测点语义——阻断反掩盖触达）；
    oob 白名单=放行；allow 集=放行；其余默认拒。返回 (verdict, reason)。"""
    h = (host or "").lower()
    if _wild_hit(acl["canary"], h):
        return "canary", "canary 域触碰=实时告警（放行留痕）"
    if _wild_hit(acl["oob"], h):
        return "oob", "OOB 回连端点（scope kind=oob 白名单）"
    if _wild_hit(acl["allow"], h):
        return "allow", "scope include 白名单"
    return "deny", "默认拒（deny-by-default）"

def build_acl(gd):
    # …既有 allow/deny/dns_pin/infra 段后追加：
    # [oob] ← scope.tsv kind=oob 生效链（amendment 后行覆盖先行，load_scope 单源复用）
    # [canary] ← scope kind=canary 行 ∪ canary/recon-decoys.tsv 部署诱饵（goal_dir 相对）

def format_log_line(now, kind, host, port, verdict):
    import time as _t
    ts = now or _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime())   # None→真墙钟；测试显式注入
    return "%s %s %s %d %s" % (ts, kind, host, port, verdict)

def append_log_line(path, line):
    _rotate_if_needed(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def _rotate_if_needed(path):
    if os.path.isfile(path) and os.path.getsize(path) > MAX_LOG_BYTES:
        for i in range(LOG_KEEP - 1, 0, -1):
            src, dst = "%s.%d" % (path, i), "%s.%d" % (path, i + 1)
            if os.path.isfile(src):
                os.replace(src, dst)
        os.replace(path, path + ".1")
```
接线：serve/serve_text 的 now 参数缺省改 None（既有显式 now 传参调用零扰动）；handler 判定改单点 `verdict, why = decide(acl, host, port)`：canary→log_line("canary", …, "ALARM")+放行；oob→放行；allow→放行；deny→拒；handler 类加 `timeout = HANDLER_TIMEOUT_S`。

- [ ] **Step 4: 跑绿+全套回归**

Run: `python3 -m unittest tests.test_egress_oob_canary_b7 tests.test_egress_proxy tests.test_canary_traffic tests.test_egress -v` → 全 OK（canary 流量级面判定词更新=行为收紧而非漂移，如实注记）；全套 discover 全绿；金样 54 面 PASS（egress 面若有=有意刷新名单）

- [ ] **Step 5: Commit**

```bash
git add cli/ledger/egress_proxy.py tests/test_egress_oob_canary_b7.py
git commit -m "批次7-T11(High)：egress OOB/canary 接线——decide 四态判定（canary 告警放行/oob 白名单/allow/默认拒）+build_acl 产 [oob]/[canary] 段（scope oob 行∪recon-decoys 诱饵）+真墙钟注入（缺省真钟/测试显式注入）+日志 5MB×3 轮转+socket 30s 超时"
```

---

### Task 12: restart 阈值消费（--usage/--round 必填+auto 档 0.75/10 轮执法）

**Files:**
- Modify: `cli/ledger/phases_engine.py:941-965`（cmd_restart 解析必填 --usage/--round）+ `run_restart:815`（签名+阈值执法+事件词带 usage/round）
- Test: `tests/test_restart_threshold_b7.py`（新）；既有 `tests/test_managed_restart.py`/`tests/test_kill9_write_fidelity.py` restart 调用统一补参

**Interfaces:**
- Produces: `tanyin-phases restart --spawn=auto|manual --usage=<0..1> --round=<n≥1> --timestamp=…`——缺参/非法值=usage exit 2；spawn=auto 须 `usage ≥ restart_context_threshold(0.75)` 或 `round % restart_every_n_rounds == 0` 否则 REJECT rc=1；manual 不设阈值但必须带参（审计语义）；事件词升级 `managed-restart spawn=<s> session=<id> usage=<u> round=<n>`（T3 孤儿解析按 token 兼容）
- Consumes: `restart_context_threshold`/`restart_every_n_rounds` 默认键=load_phases 单源（phases_engine.py:195 既有，禁第二常量源）

- [ ] **Step 1: 写失败测试（红=阈值零消费）**

```python
# tests/test_restart_threshold_b7.py
# -*- coding: utf-8 -*-
"""批次 7 T12：restart 阈值接线（High：≥0.75/≥10 轮全仓零代码消费）。
红=缺参/低用量照常重启。"""
import os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from tests.test_dryrun_p0p2 import fresh_drydir, ledger, phases, TS

class TestRestartThreshold(unittest.TestCase):
    def _ready(self, td, name):
        gd = fresh_drydir(td.name, name)
        ledger(gd, "checkpoint", ["--session=s0", "--phase=P1", "--note=init",
                                  "--timestamp=2026-09-27T00:00:00Z"])
        return gd

    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup)

    def test_missing_usage_round_exit_2(self):
        gd = self._ready(self.td, "G-r1")
        rc, out, err = phases(gd, "restart", ["--spawn=auto", "--timestamp=2026-09-27T01:00:00Z"])
        self.assertEqual(rc, 2, "红现状：缺 --usage/--round 照常受理")

    def test_auto_below_threshold_rejected(self):
        gd = self._ready(self.td, "G-r2")
        rc, out, err = phases(gd, "restart", ["--spawn=auto", "--usage=0.30", "--round=3",
                                              "--timestamp=2026-09-27T01:00:00Z"])
        self.assertEqual(rc, 1, "红现状：0.30/3 轮照样重启（阈值零消费）")
        self.assertIn("restart-threshold", out)

    def test_auto_at_context_threshold_passes(self):
        gd = self._ready(self.td, "G-r3")
        rc, out, err = phases(gd, "restart", ["--spawn=auto", "--usage=0.80", "--round=3",
                                              "--timestamp=2026-09-27T01:00:00Z"])
        self.assertEqual(rc, 0, out + err)

    def test_auto_every_n_rounds_passes(self):
        gd = self._ready(self.td, "G-r4")
        rc, out, err = phases(gd, "restart", ["--spawn=auto", "--usage=0.10", "--round=10",
                                              "--timestamp=2026-09-27T01:00:00Z"])
        self.assertEqual(rc, 0, out + err)

    def test_manual_records_without_threshold(self):
        gd = self._ready(self.td, "G-r5")
        rc, out, err = phases(gd, "restart", ["--spawn=manual", "--usage=0.10", "--round=3",
                                              "--timestamp=2026-09-27T01:00:00Z"])
        self.assertEqual(rc, 0, out + err)
        tl = open(os.path.join(gd, "timeline.tsv"), encoding="utf-8").read()
        self.assertIn("usage=0.1", tl.replace("usage=0.10", "usage=0.1"), "事件词带 usage/round 审计")

    def test_invalid_values_exit_2(self):
        gd = self._ready(self.td, "G-r6")
        for extra in (["--usage=1.5", "--round=3"], ["--usage=abc", "--round=3"],
                      ["--usage=0.5", "--round=0"], ["--usage=0.5", "--round=x"]):
            rc, out, err = phases(gd, "restart",
                                  ["--spawn=auto", "--timestamp=2026-09-27T01:00:00Z"] + extra)
            self.assertEqual(rc, 2, "非法值=usage 错: %r" % extra)
```

- [ ] **Step 2: 跑红**

Run: `python3 -m unittest tests.test_restart_threshold_b7 -v`
Expected: 缺参例 FAIL（rc=0/1 非 2）；低用量例 FAIL（rc=0）；其余例视实现时点

- [ ] **Step 3: 最小实现**

```python
# cli/ledger/phases_engine.py cmd_restart（:941-965）：解析两新参+校验
        usage = rnd = None
        for tok in rest:
            if tok.startswith("--usage="):
                usage = tok.split("=", 1)[1]
            elif tok.startswith("--round="):
                rnd = tok.split("=", 1)[1]
        try:
            u = float(usage)
            if not (0.0 <= u <= 1.0):
                raise ValueError
        except (TypeError, ValueError):
            sys.stderr.write("用法错误: --usage 须 0..1\n")
            return 2
        try:
            n = int(rnd)
            if n < 1:
                raise ValueError
        except (TypeError, ValueError):
            sys.stderr.write("用法错误: --round 须正整数\n")
            return 2
        # 透传 run_restart(..., usage=u, round_no=n)
```

```python
# run_restart 内（⓪孤儿对账后、③单活跃会话前）：
    # 阈值执法（批次 7 T12，High：≥0.75/≥10 轮全仓零消费→接线；单源=load_phases 默认键）
    if spawn == "auto":
        thr = float(PHASES_DEFAULTS["restart_context_threshold"])
        every = int(PHASES_DEFAULTS["restart_every_n_rounds"])
        if not (u >= thr or n % every == 0):
            print("REJECT\trestart\trestart-threshold usage=%.2f round=%d 未达（≥%.2f 或 每 %d 轮）"
                  % (u, n, thr, every))
            return 1
    # ⑤事件词升级：
    _append_event(goal_dir, gate, "managed-restart spawn=%s session=%s usage=%g round=%d%s"
                  % (spawn, session, u, n, takeover), ts)
```
（PHASES_DEFAULTS=load_phases 默认键取用位——以 :195 实名对齐；既有 test_managed_restart 10 例与 T3 kill9 孤儿例 restart 调用统一补 `--usage=0.90 --round=1`，属必填参数契约后果非语义变更。）

- [ ] **Step 4: 跑绿+全套回归**

Run: `python3 -m unittest tests.test_restart_threshold_b7 tests.test_managed_restart tests.test_kill9_write_fidelity -v` → 全 OK；全套 discover 全绿；金样 54 面 PASS 零漂移

- [ ] **Step 5: Commit**

```bash
git add cli/ledger/phases_engine.py tests/test_restart_threshold_b7.py tests/test_managed_restart.py tests/test_kill9_write_fidelity.py
git commit -m "批次7-T12(High)：restart 阈值消费——--usage/--round 必填（缺参/非法=exit 2）+auto 档 0.75/10 轮阈值执法（单源=phases 默认键）+manual 带参审计；事件词带 usage/round；既有重启面统一补参（必填契约后果）"
```

---

（T13→T17 正文增量补齐中……）





