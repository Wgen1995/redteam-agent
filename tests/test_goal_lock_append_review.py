# -*- coding: utf-8 -*-
"""批次 7 评审收尾 I-3：五工具 append 接 goal 锁（T2 锁面遗漏的另一半）。

红=评审并发反例：tanyin-guard/tanyin-canary/tanyin-egress/tanyin-replay/
tanyin-budgetctl 五工具各自 append_tl 直写 timeline.tsv 不经 registry._locked
（读表→算链→写回全窗口无锁）——16 并发 egress compile 竞速=lost-update 丢事件
（后写者以同一 prev 落行、先写者整行蒸发），链哈希看似完整而事件缺失，与 C1
「并发安全」目标相悖。

绿=五工具 append_tl 全部接入 ledger.filelock.goal_lock（filelock 单源，复用
registry._locked 锁形：锁包「读表→改内存→commit」全程）；16 并发全 rc=0+
16 事件全存活+verify-chain PASS。同批收口 set-replay-state 写路径（R-T2-2
遗留）：handler 内部锁住「读账→落 timeline→联动 findings」全程（用法校验
先行于锁，UsageError 路径零持锁），登记 b7 台账。

夹具=R-T2-1 同律：G-g1 拷贝（fresh 目录无 goals 行撞 Tier0 硬门=假红）。
"""
import os, shutil, subprocess, sys, tempfile, unittest
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)
from ledger import core

CLI = os.path.join(ROOT, "cli")
FIX = os.path.join(HERE, "fixtures", "G-g1")
EGRESS = os.path.join(CLI, "tanyin-egress")
CANARY = os.path.join(CLI, "tanyin-canary")
BUDGET = os.path.join(CLI, "tanyin-budgetctl")
GUARD = os.path.join(CLI, "tanyin-guard")
REPLAY = os.path.join(CLI, "tanyin-replay")
TS = "2026-09-23T03:00:00Z"
NCOL = len(core.TABLES["timeline.tsv"])


def run(tool, *args):
    return subprocess.run([sys.executable, tool] + list(args),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=180)


def _events(gd, prefix):
    p = os.path.join(gd, "timeline.tsv")
    rows = core.read_tsv(p, NCOL)
    ei = core.TABLES["timeline.tsv"].index("event")
    return [r for r in rows if r[ei].startswith(prefix)]


class TestConcurrentAppendLock(unittest.TestCase):
    """红=16 并发 egress compile 丢事件复现（lost-update 反例）；绿=全存活+链完整。"""

    def test_sixteen_concurrent_compiles_all_events_survive(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        gd = shutil.copytree(FIX, os.path.join(tmp.name, "G-g1"))
        n0 = len(_events(gd, "egress-compile"))
        def one(_i):
            return run(EGRESS, "compile", "--goal-dir", gd)
        with ThreadPoolExecutor(max_workers=16) as ex:
            results = list(ex.map(one, range(16)))
        bad = [(r.returncode, (r.stdout + r.stderr)[:150]) for r in results if r.returncode != 0]
        self.assertEqual(bad, [], "16 并发全 rc=0：%s" % bad[:3])
        got = len(_events(gd, "egress-compile"))
        self.assertEqual(got, n0 + 16,
                         "16 个 egress-compile 事件一个不能少（专家反例：lost-update 蒸发行）")
        r = run(os.path.join(CLI, "tanyin-ledger"), "verify-chain", "--goal-dir", gd)
        self.assertEqual(r.returncode, 0, "并发后链完整: " + r.stdout + r.stderr)


class TestFiveToolAppendLocked(unittest.TestCase):
    """五工具 append 路径逐一落事件+全链 verify-chain PASS（接线面回归）。"""

    def test_five_tool_appends_landed_and_chained(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        gd = shutil.copytree(FIX, os.path.join(tmp.name, "G-g1"))
        # ① egress compile
        r = run(EGRESS, "compile", "--goal-dir", gd)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # ② canary recon-deploy + recon-recall
        r = run(CANARY, "recon-deploy", "--goal-dir", gd,
                "--value=canary.fixture.example", "--type=subdomain", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(CANARY, "recon-recall", "--goal-dir", gd)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # ③ budgetctl rate 超窗熔断（budget.tsv 注入超限行→REJECT rc=1 落 budgetctl-reject）
        bp = os.path.join(gd, "budget.tsv")
        with open(bp, "a", encoding="utf-8", newline="\n") as f:
            f.write("2026-09-23T02:05:00Z\t0\t99999\t0\t0\tgoal\tprobe\t2\n")
        r = run(BUDGET, "rate", "--goal-dir", gd,
                "--now=2026-09-23T02:06:00Z", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1, "rate 超限须 REJECT rc=1: " + r.stdout + r.stderr)
        # ④ guard exec 界外 REJECT（scope 门先行拦截，零真实执行）
        r = run(GUARD, "exec", "--goal-dir", gd, "--", "curl", "http://evil.example/")
        self.assertEqual(r.returncode, 1, "界外须 REJECT rc=1: " + r.stdout + r.stderr)
        # ⑤ replay env-diff（预铸 EV 卡片，连接层失败确定性——R-T5-4 同口径）
        ep = os.path.join(gd, "E-index.tsv")
        ev = [l.split("\t")[0] for l in open(ep, encoding="utf-8").read().splitlines() if l][0]
        card = os.path.join(gd, "evidence", ev + ".md")
        os.makedirs(os.path.dirname(card), exist_ok=True)
        with open(card, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\nid: %s\nnetwork_position: internet\n"
                    "raw_request: |\n  GET /x HTTP/1.1\n  Host: 10.10.9.9\n"
                    "expected: {}\npair_group: \n---\n## 摘\n" % ev)
        r = run(REPLAY, "replay", "--goal-dir", gd, "--id=" + ev,
                "--scheme=http", "--port=1", "--timeout=2", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # 五工具事件词逐一在场
        tl = open(os.path.join(gd, "timeline.tsv"), encoding="utf-8").read()
        for word in ("egress-compile", "recon-decoy-deploy", "recon-decoy-recall",
                     "budgetctl-reject", "guard-reject out-of-scope host=evil.example",
                     "request: 10.10.9.9/x via=replay"):
            self.assertIn(word, tl, "事件词缺失: " + word)
        r = run(os.path.join(CLI, "tanyin-ledger"), "verify-chain", "--goal-dir", gd)
        self.assertEqual(r.returncode, 0, "五工具混写后链完整: " + r.stdout + r.stderr)


class TestSetReplayStateLocked(unittest.TestCase):
    """R-T2-2 遗留收口：set-replay-state 写路径持锁（行为面零变更，并发不丢事件）。"""

    def test_set_replay_state_appends_and_chains(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        gd = shutil.copytree(FIX, os.path.join(tmp.name, "G-g1"))
        r = run(os.path.join(CLI, "tanyin-ledger"), "set-replay-state",
                "--goal-dir", gd, "--id=EV-g1-0001", "--state=VERIFIED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(_events(gd, "replay:EV-g1-0001:VERIFIED")), 1)
        r = run(os.path.join(CLI, "tanyin-ledger"), "verify-chain", "--goal-dir", gd)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
