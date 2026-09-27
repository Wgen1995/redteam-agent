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

（T4→T17 正文增量补齐中……）


