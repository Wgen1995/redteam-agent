# -*- coding: utf-8 -*-
"""多任务治理舰（功能25补件）·件②：仗注册表 fleet_state——TDD 红测试先行。

设计源：docs/design/2026-10-20-build-master-plan.md R14「多任务治理舰」+
裁决书 §十八（supervisor 舰队化缺三件之一=注册表面）。审计实证
（docs/research/2026-10-20-assets-inventory-audit.md :75）：十并发/排队=纯设计，
本件把「仗注册表」落成 TSV 单源 + 追加审计。

Ruling（写测试即写契约）：
- R-FLS-1 TSV 单源：fleet.tsv=仗注册表（battle/goal_dir/state/soldiers/priority/
  budget_usd/budget_cap_usd/deadline/heartbeat_at/queued_at/updated_at 11 列）；
  fleet-meta.tsv=舰队级旗（key/value/updated_at——halted 落此，不塞 battles 行）；
  fleet-audit.tsv=追加审计（ts/actor/action/battle/detail，只追加不改写）。
- R-FLS-2 状态机 active-paused-done-failed+queued：queued→{active,paused,failed}；
  active→{paused,done,failed}；paused→{active,queued,done,failed}（paused→queued=
  续仗遇帽排队）；done/failed 终态——出终态转移=ValueError（fail-loud 程序错）。
  同态转移=幂等 no-op（changed=False 零审计追加）。
- R-FLS-3 幂等律：register 重复=already-registered 零写入零审计；soldiers 无变化
  =零审计；set_meta 同值=零审计。一切变更动作原子写（tmp+rename）。
- R-FLS-4 心跳超时检测=纯读：active 行 heartbeat_at 缺失或 now-heartbeat>timeout
  →stale；paused/queued/done/failed 不参与（不执法停摆的仗）。
- R-FLS-5 损坏 fleet.tsv=fail-closed ValueError（battle_registry 同律：零静默重置）；
  battle 名须 battle-N 形。
- R-FLS-6 钟全注入：所有写入口收 now_iso 字符串（ISO Z 形），stale 检测收
  now_epoch——注册表零取钟（判决可测）。

跑法：python3 -m unittest tests.test_fleet_state -v
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from fleet import fleet_state as fs  # noqa: E402

from ledger.enforce import parse_ts  # noqa: E402

TS1 = "2026-10-20T08:00:00Z"
TS2 = "2026-10-20T09:00:00Z"
TS3 = "2026-10-20T10:00:00Z"
E1 = parse_ts(TS1)
E3 = parse_ts(TS3)


def _audit_count(root):
    return len(fs.audit_rows(root))


class TestRegister(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def test_register_creates_queued_row_and_audit(self):
        v = fs.register(self.root, "battle-1", "/tmp/b1/G-w1",
                        soldiers=3, now_iso=TS1)
        self.assertTrue(v["registered"])
        self.assertEqual(v["row"]["state"], "queued")
        self.assertEqual(v["row"]["soldiers"], "3")
        self.assertEqual(v["row"]["goal_dir"], "/tmp/b1/G-w1")
        row = fs.row_of(self.root, "battle-1")
        self.assertEqual(row["state"], "queued")
        self.assertEqual(row["queued_at"], TS1)
        audits = fs.audit_rows(self.root)
        self.assertEqual(len(audits), 1)
        self.assertEqual(audits[0]["action"], "register")
        self.assertEqual(audits[0]["battle"], "battle-1")

    def test_register_duplicate_idempotent(self):
        fs.register(self.root, "battle-1", "/tmp/b1/G-w1", soldiers=3, now_iso=TS1)
        n = _audit_count(self.root)
        v = fs.register(self.root, "battle-1", "/tmp/b1/G-w1", soldiers=5,
                        now_iso=TS2)
        self.assertFalse(v["registered"])
        self.assertEqual(v["reason"], "already-registered")
        self.assertEqual(v["row"]["soldiers"], "3")   # 原行不动
        self.assertEqual(_audit_count(self.root), n)  # 零审计追加
        self.assertEqual(len(fs.rows(self.root)), 1)

    def test_register_bad_name_raises(self):
        for bad in ("foo", "battle-", "battle-x", ""):
            with self.assertRaises(ValueError):
                fs.register(self.root, bad, "/tmp/x", now_iso=TS1)

    def test_register_default_fields(self):
        fs.register(self.root, "battle-2", "/tmp/b2", now_iso=TS1)
        r = fs.row_of(self.root, "battle-2")
        self.assertEqual(r["soldiers"], "0")
        self.assertEqual(r["priority"], "")
        self.assertEqual(r["deadline"], "")
        self.assertEqual(r["heartbeat_at"], "")


class TestStateMachine(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        fs.register(self.root, "battle-1", "/tmp/b1", now_iso=TS1)

    def test_queued_to_active(self):
        v = fs.transition(self.root, "battle-1", "active", now_iso=TS2)
        self.assertTrue(v["changed"])
        self.assertEqual(v["from"], "queued")
        self.assertEqual(v["to"], "active")
        self.assertEqual(fs.row_of(self.root, "battle-1")["state"], "active")

    def test_active_pause_resume_roundtrip(self):
        fs.transition(self.root, "battle-1", "active", now_iso=TS2)
        fs.transition(self.root, "battle-1", "paused", now_iso=TS2)
        v = fs.transition(self.root, "battle-1", "active", now_iso=TS3)
        self.assertTrue(v["changed"])
        self.assertEqual(fs.row_of(self.root, "battle-1")["state"], "active")

    def test_active_to_done_and_failed(self):
        for i, terminal in enumerate(("done", "failed")):
            b = "battle-%d" % (11 + i)
            fs.register(self.root, b, "/tmp/bx", now_iso=TS1)
            fs.transition(self.root, b, "active", now_iso=TS2)
            fs.transition(self.root, b, terminal, now_iso=TS3)
            self.assertEqual(fs.row_of(self.root, b)["state"], terminal)

    def test_terminal_states_are_frozen(self):
        for i, terminal in enumerate(("done", "failed")):
            b = "battle-%d" % (9 + i)
            fs.register(self.root, b, "/tmp/bx", now_iso=TS1)
            fs.transition(self.root, b, "active", now_iso=TS2)
            fs.transition(self.root, b, terminal, now_iso=TS3)
            self.assertEqual(fs.row_of(self.root, b)["state"], terminal)
            for nxt in ("active", "paused", "queued"):
                with self.assertRaises(ValueError):
                    fs.transition(self.root, b, nxt, now_iso=TS3)

    def test_queued_to_paused_allowed(self):
        """停一个排队仗（未开打先停）=合法——全停阀传播到所有仗的执法面。"""
        v = fs.transition(self.root, "battle-1", "paused", now_iso=TS2)
        self.assertTrue(v["changed"])

    def test_paused_to_queued_allowed(self):
        """续仗遇帽排队：paused→queued 合法（排队不开工）。"""
        fs.transition(self.root, "battle-1", "active", now_iso=TS2)
        fs.transition(self.root, "battle-1", "paused", now_iso=TS2)
        v = fs.transition(self.root, "battle-1", "queued", now_iso=TS3)
        self.assertTrue(v["changed"])

    def test_illegal_transition_raises(self):
        with self.assertRaises(ValueError):     # queued→done 绕道终态=程序错
            fs.transition(self.root, "battle-1", "done", now_iso=TS2)

    def test_same_state_transition_idempotent(self):
        fs.transition(self.root, "battle-1", "active", now_iso=TS2)
        n = _audit_count(self.root)
        v = fs.transition(self.root, "battle-1", "active", now_iso=TS3)
        self.assertFalse(v["changed"])
        self.assertEqual(_audit_count(self.root), n)

    def test_unknown_battle_raises(self):
        with self.assertRaises(ValueError):
            fs.transition(self.root, "battle-404", "active", now_iso=TS1)

    def test_bad_state_raises(self):
        with self.assertRaises(ValueError):
            fs.transition(self.root, "battle-1", "running", now_iso=TS1)

    def test_transition_appends_audit(self):
        fs.transition(self.root, "battle-1", "active", now_iso=TS2, reason="promote")
        a = fs.audit_rows(self.root)[-1]
        self.assertEqual(a["action"], "transition")
        self.assertIn("queued", a["detail"])
        self.assertIn("active", a["detail"])
        self.assertIn("promote", a["detail"])


class TestSoldiersAndHeartbeat(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        fs.register(self.root, "battle-1", "/tmp/b1", soldiers=2, now_iso=TS1)

    def test_set_soldiers_updates_and_audits(self):
        v = fs.set_soldiers(self.root, "battle-1", 5, now_iso=TS2)
        self.assertEqual(v["soldiers"], 5)
        self.assertTrue(v["changed"])
        self.assertEqual(fs.row_of(self.root, "battle-1")["soldiers"], "5")
        self.assertEqual(fs.audit_rows(self.root)[-1]["action"], "set-soldiers")

    def test_set_soldiers_negative_raises(self):
        with self.assertRaises(ValueError):
            fs.set_soldiers(self.root, "battle-1", -1, now_iso=TS2)

    def test_set_soldiers_nochange_no_audit(self):
        fs.set_soldiers(self.root, "battle-1", 2, now_iso=TS2)
        n = _audit_count(self.root)
        v = fs.set_soldiers(self.root, "battle-1", 2, now_iso=TS3)
        self.assertFalse(v["changed"])
        self.assertEqual(_audit_count(self.root), n)

    def test_heartbeat_updates_row(self):
        fs.heartbeat(self.root, "battle-1", now_iso=TS2)
        self.assertEqual(fs.row_of(self.root, "battle-1")["heartbeat_at"], TS2)
        self.assertEqual(fs.row_of(self.root, "battle-1")["updated_at"], TS2)

    def test_stale_detects_timeout(self):
        fs.transition(self.root, "battle-1", "active", now_iso=TS1)
        fs.heartbeat(self.root, "battle-1", now_iso=TS1)
        self.assertEqual(fs.stale_battles(self.root, E1 + 3600.0, 900.0),
                         ["battle-1"])

    def test_stale_missing_heartbeat_counts(self):
        fs.transition(self.root, "battle-1", "active", now_iso=TS1)
        self.assertEqual(fs.stale_battles(self.root, E1 + 3600.0, 900.0),
                         ["battle-1"])

    def test_stale_fresh_not_flagged(self):
        fs.transition(self.root, "battle-1", "active", now_iso=TS1)
        fs.heartbeat(self.root, "battle-1", now_iso=TS2)
        self.assertEqual(fs.stale_battles(self.root, E1 + 600.0, 900.0), [])

    def test_stale_ignores_non_active(self):
        fs.heartbeat(self.root, "battle-1", now_iso=TS1)   # 仍 queued
        self.assertEqual(fs.stale_battles(self.root, E3, 900.0), [])


class TestMeta(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def test_set_meta_upsert_and_audit(self):
        fs.set_meta(self.root, "halted", "1", now_iso=TS1, reason="emergency")
        self.assertEqual(fs.meta(self.root).get("halted"), "1")
        fs.set_meta(self.root, "halted", "0", now_iso=TS2, reason="clear")
        m = fs.meta(self.root)
        self.assertEqual(m.get("halted"), "0")
        self.assertEqual(len(fs.audit_rows(self.root)), 2)

    def test_set_meta_same_value_idempotent(self):
        fs.set_meta(self.root, "halted", "1", now_iso=TS1, reason="a")
        n = _audit_count(self.root)
        v = fs.set_meta(self.root, "halted", "1", now_iso=TS2, reason="b")
        self.assertFalse(v["changed"])
        self.assertEqual(_audit_count(self.root), n)
        self.assertEqual(fs.meta(self.root).get("halted"), "1")

    def test_meta_missing_root_empty(self):
        self.assertEqual(fs.meta(self.root), {})


class TestDiscipline(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def test_corrupt_fleet_tsv_fails_closed(self):
        p = os.path.join(self.root, fs.FLEET_TSV)
        os.makedirs(self.root, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write("not\tactual\tcolumns\n")
        with self.assertRaises(ValueError):
            fs.rows(self.root)

    def test_snapshot_sorted_with_totals(self):
        fs.register(self.root, "battle-2", "/tmp/b2", soldiers=3, now_iso=TS1)
        fs.register(self.root, "battle-10", "/tmp/b10", soldiers=2, now_iso=TS1)
        fs.register(self.root, "battle-1", "/tmp/b1", soldiers=1, now_iso=TS1)
        fs.transition(self.root, "battle-2", "active", now_iso=TS2)
        fs.transition(self.root, "battle-10", "active", now_iso=TS2)
        snap = fs.snapshot(self.root)
        # 自然序：battle-1 < battle-2 < battle-10（数字序非字典序）
        self.assertEqual([b["battle"] for b in snap["battles"]],
                         ["battle-1", "battle-2", "battle-10"])
        self.assertEqual(snap["totals"]["active_soldiers"], 5)
        self.assertEqual(snap["totals"]["by_state"]["active"], 2)
        self.assertEqual(snap["totals"]["by_state"]["queued"], 1)

    def test_atomic_write_no_temp_leftover(self):
        fs.register(self.root, "battle-1", "/tmp/b1", now_iso=TS1)
        leftovers = [n for n in os.listdir(self.root)
                     if n.startswith(".") or n.endswith(".tmp")]
        self.assertEqual(leftovers, [])

    def test_row_of_unknown_none(self):
        self.assertIsNone(fs.row_of(self.root, "battle-404"))

    def test_audit_rows_shape(self):
        fs.register(self.root, "battle-1", "/tmp/b1", now_iso=TS1)
        a = fs.audit_rows(self.root)[0]
        self.assertEqual(
            sorted(a.keys()), ["action", "actor", "battle", "detail", "ts"])
        self.assertEqual(a["ts"], TS1)
        self.assertEqual(a["actor"], fs.ACTOR)


if __name__ == "__main__":
    unittest.main()
