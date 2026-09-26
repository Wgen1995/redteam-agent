# -*- coding: utf-8 -*-
"""批次 6 T7：G-5 锁收紧（裁决 F）——state.md 锁字段 v2+OS 级探活快路。

行为面（计划冻结）：
- probe_stale：本机同 boot 且 pid 死=dead（manual 免 rebuild 快路）；pid 活=alive；
  跨机/跨 boot/字段缺=unknown（保守——auto 恒 REJECT、manual 维持对账前置，现状逐字节）。
- auto 接管恒不放行（单活跃会话铁律，probe==dead 也不放）。
- 既有 test_managed_restart 七例行为零改动（本文件 wiring 三例为增量面）。"""
import io, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import core, lock_v2, phases_engine as pe, state_md  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
T0 = "2026-09-24T10:00:00Z"
T2 = "2026-09-24T10:20:00Z"   # 距 T0 20 分钟 > 10 分钟速率窗


class TestProbe(unittest.TestCase):
    def test_dead_same_host_dead_pid(self):
        f = {"lock_host": lock_v2.HOST, "lock_boot": lock_v2.BOOT,
             "lock_pid": lock_v2.DEAD_PID}
        self.assertEqual(lock_v2.probe_stale(f)[0], "dead")

    def test_alive_same_host(self):
        f = {"lock_host": lock_v2.HOST, "lock_boot": lock_v2.BOOT,
             "lock_pid": os.getpid()}
        self.assertEqual(lock_v2.probe_stale(f)[0], "alive")

    def test_cross_host_unknown(self):
        f = {"lock_host": "other", "lock_boot": "b", "lock_pid": 1}
        self.assertEqual(lock_v2.probe_stale(f)[0], "unknown")

    def test_v1_fields_absent_unknown(self):
        self.assertEqual(lock_v2.probe_stale({})[0], "unknown")

    def test_boot_id_stable(self):
        self.assertEqual(lock_v2.boot_id(), lock_v2.boot_id())


class Base(unittest.TestCase):
    """夹具=test_managed_restart 同型（G-g1 副本+dispatch restart）。"""

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

    def write_lock(self, lock=None, revision="0", session="s-owner"):
        """手置 state.md 锁（revision 缺省错位=若对账前置未免，必 REJECT——快路证明面）。"""
        fields = {
            "revision": revision,
            "goal": "G-g1-0001",
            "phase": "",
            "round": "0",
            "session": session,
            "session_status": "active",
            "spawn": "manual",
            "updated": T0,
            "resume_kit": "resume-kit.md",
            "snapshot": state_md.snapshot_from_session(core.Session(self.gd)),
        }
        if lock is not None:
            fields.update({"lock_host": lock[0], "lock_pid": str(lock[1]),
                           "lock_boot": lock[2], "lock_since": T0})
        state_md.write_state(os.path.join(self.gd, "state.md"), fields, [])


class TestRestartWiring(Base):
    def test_manual_fast_path_no_rebuild(self):
        # 前置：state.md 手置 dead 锁（本机+死 pid+lock_since=T0）；revision 错位
        # ——免 rebuild 快路才可能 OK（旧语义必 state-rebuild 未过 REJECT rc=1）
        self.write_lock(lock=(lock_v2.HOST, lock_v2.DEAD_PID, lock_v2.BOOT))
        code, out, err = self.restart("--spawn=manual", "--timestamp=" + T2,
                                      "--session=s-new")
        self.assertEqual(code, 0, out + err)
        hit = [e for e in self.events() if e.startswith("managed-restart")]
        self.assertTrue(any("takeover-of=" in e and "probe=pid-dead" in e
                            for e in hit), str(hit))
        # 接管后新会话持 v2 锁（锁交接闭环：锁字段=新进程 OS 事实）
        f, _, errs = state_md.parse_state(os.path.join(self.gd, "state.md"))
        self.assertEqual(errs, [])
        self.assertEqual(f["session"], "s-new")
        self.assertEqual(f["lock_pid"], str(os.getpid()))

    def test_unknown_lock_manual_still_requires_rebuild(self):
        # 跨机锁=探测不出=保守：manual 未过对账前置前 REJECT（现状语义回退断言）
        self.write_lock(lock=("other-host", 1, "b"))
        before = self.snap_bytes()
        code, out, _ = self.restart("--spawn=manual", "--timestamp=" + T2,
                                    "--session=s-new")
        self.assertEqual(code, 1)
        self.assertIn("state-rebuild 未过", out)
        self.assertEqual(self.snap_bytes(), before)   # REJECT 零副作用

    def test_state_fields_written_on_restart(self):
        # 正常 restart 后 parse_state fields 含 lock_host/lock_pid/lock_boot/lock_since
        code, out, err = self.restart("--spawn=auto", "--timestamp=" + T0)
        self.assertEqual(code, 0, out + err)
        f, _, errs = state_md.parse_state(os.path.join(self.gd, "state.md"))
        self.assertEqual(errs, [])
        self.assertEqual(f["lock_host"], lock_v2.HOST)
        self.assertEqual(f["lock_pid"], str(os.getpid()))
        self.assertEqual(f["lock_boot"], lock_v2.BOOT)
        self.assertEqual(f["lock_since"], T0)

    def snap_bytes(self):
        out = {}
        paths = [(t, os.path.join(self.gd, t)) for t in core.TABLES]
        paths.append(("state.md", os.path.join(self.gd, "state.md")))
        for name, p in paths:
            out[name] = read_bytes(p)
        return out


def read_bytes(p):
    if not os.path.exists(p):
        return None
    with open(p, "rb") as f:
        return f.read()


if __name__ == "__main__":
    unittest.main()
