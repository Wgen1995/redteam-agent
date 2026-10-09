# -*- coding: utf-8 -*-
"""P0 诚实性加固批（2026-10-10 九维专家会诊·缺口①）：VERIFIED 自证洞。

会诊诊断（AI agent 专家 #1）：set-replay-state 唯一机械拦截是
not-reproduced 拒签——无探针行静默放行=战士可完全不跑 replay 逐条
自证 VERIFIED。本批：无 reproduced 实证 ⇒ REJECT（rc=1）；--manual=1
显式人工通道放行但事件带 note=manual 标记；not-reproduced 最新裁决
连 --manual 也拒（事实矛盾须补探针翻案）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T10:00:00Z"


def run(gd, *args):
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestProbeRequired(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def _probe(self, verdict, ts, rid="EV-g1-0001"):
        r = run(self.d, "append-timeline", "--actor=子代理", "--phase=P4",
                "--event=replay-probe %s verdict=%s" % (rid, verdict),
                "--revert-cmd=none", "--timestamp=" + ts)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_verified_without_probe_rejected(self):
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("replay-probe reproduced", r.stderr + r.stdout)

    def test_verified_with_reproduced_probe_passes(self):
        self._probe("reproduced", "2026-09-29T16:00:00Z")
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_manual_channel_marks_event(self):
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED",
                "--timestamp=" + TS, "--manual=1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        tl = open(os.path.join(self.d, "timeline.tsv"), encoding="utf-8").read()
        self.assertIn("replay:EV-g1-0001:VERIFIED note=manual", tl)

    def test_manual_cannot_override_not_reproduced(self):
        self._probe("not-reproduced", "2026-09-29T16:00:00Z")
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED",
                "--timestamp=" + TS, "--manual=1")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("not-reproduced", r.stderr + r.stdout)

    def test_fd_via_linked_ev_probe(self):
        # FD 通道：直铸一枚挂接 EV（linked_finding=FD-g1-0001，E-index 非链式表
        # 可直写），其 reproduced 探针 ⇒ FD 可签；无任何挂接探针 ⇒ FD 拒
        idx = os.path.join(self.d, "E-index.tsv")
        with open(idx, encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        li = 11  # schemas.json E-index.tsv: linked_finding（夹具无表头行）
        row = ["EV-g1-0002", "挂接证据", "command", TS, "internet",
               "curl -s http://x/", "single", "a" * 64, "b" * 64, "", "",
               "FD-g1-0001", "", "ex", "2", TS]
        lines.append("\t".join(row))
        with open(idx, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        self._probe("reproduced", "2026-09-29T16:00:00Z", rid="EV-g1-0002")
        r = run(self.d, "set-replay-state", "--id=FD-g1-0001", "--state=VERIFIED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_fd_without_any_probe_rejected(self):
        r = run(self.d, "set-replay-state", "--id=FD-g1-0001", "--state=VERIFIED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_rejected_state_unaffected(self):
        # REJECTED 与实证无关，不受新门影响
        r = run(self.d, "set-replay-state", "--id=EV-g1-0001", "--state=REJECTED",
                "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
