# -*- coding: utf-8 -*-
"""C2-lite 域账本测试——表 schema/append-only 哈希链/beacon 心跳投影/指令队列
行号游标/回显证据化/L3 预授权审批族。全例本地回环(tmp goal+127.0.0.1 口径,
零外网零真靶零墙钟睡眠)。"""
import hashlib
import os
import unittest

from ledger import core as ledger_core
from ledger.core import Session
from test_c2_common import T0, add_intent, boot_beacon, boot_c2, boot_goal, grant_family, ts

from cli.c2 import beacon, echo, families, queue
from cli.c2.store import C2Error, C2Store
from cli.c2.tables import C2_TABLES, ECHO_ARTIFACT_THRESHOLD, EXCERPT_MAX, HEARTBEAT_TIMEOUT


class TestTablesStore(unittest.TestCase):
    """表=schema 冻结面: 未知表 fail-closed,链自 Genesis 起,篡改可检。"""

    def setUp(self):
        self.d, self.gd = boot_goal()
        self.addCleanup(self.d.cleanup)
        self.store = C2Store(self.gd)

    def _cmd_fields(self, n):
        return {"id": "CMD-c2t-%04d" % n, "beacon_id": "BCN-c2t-0001", "argv": "id",
                "enqueued_at": T0, "approval_ref": "", "note": ""}

    def test_cols_unknown_table_fail_closed(self):
        from cli.c2 import tables
        with self.assertRaises(ValueError):
            tables.cols("nope.tsv")

    def test_dict_row_missing_field_rejected(self):
        from cli.c2 import tables
        with self.assertRaises(ValueError):
            tables.dict_row("cmds.tsv", {"id": "x"})

    def test_append_chains_from_genesis(self):
        ci = C2_TABLES["cmds.tsv"]
        r1 = self.store.append("cmds.tsv", self._cmd_fields(1))
        r2 = self.store.append("cmds.tsv", self._cmd_fields(2))
        self.assertEqual(r1[ci.index("prev_hash")], ledger_core.GENESIS, "首行 prev=GENESIS")
        self.assertEqual(r2[ci.index("prev_hash")], r1[ci.index("hash")], "链经 prev 延续")
        self.assertEqual(self.store.verify_chains()["cmds.tsv"], 0, "全链完整")

    def test_verify_chains_detects_tamper(self):
        self.store.append("cmds.tsv", self._cmd_fields(1))
        self.store.append("cmds.tsv", dict(self._cmd_fields(2), argv="uname -a"))
        p = self.store.path("cmds.tsv")
        with open(p, "r", encoding="utf-8") as f:
            text = f.read()
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text.replace("uname -a", "uname -x"))
        self.assertEqual(self.store.verify_chains()["cmds.tsv"], 2, "第 2 行篡改=断链可检")

    def test_read_numbered_stable_and_latest_wins(self):
        self.store.append("beacons.tsv", {
            "id": "BCN-c2t-0001", "kind": "register", "ts": T0, "intent_ref": "I",
            "cred_ref": "", "host_tag": "", "note": ""})
        self.store.append("beacons.tsv", {
            "id": "BCN-c2t-0001", "kind": "heartbeat", "ts": ts(1), "intent_ref": "I",
            "cred_ref": "", "host_tag": "", "note": ""})
        self.assertEqual([n for n, _ in self.store.read_numbered("beacons.tsv")], [1, 2],
                         "行号=物理行序(append-only 下稳定=游标域)")
        fam = self.store.latest_by_key("beacons.tsv")
        self.assertEqual(fam["BCN-c2t-0001"][1], "heartbeat", "行族投影: 同 id 最新行胜")


class TestBeacon(unittest.TestCase):
    """beacon=账本行: 引用闭合 fail-closed,心跳超时=投影翻转非改行。"""

    def setUp(self):
        self.d, self.gd, self.iid = boot_c2()
        self.addCleanup(self.d.cleanup)

    def test_register_unknown_intent_rejected(self):
        with self.assertRaises(C2Error):
            beacon.register(self.gd, T0, "INT-c2t-9999")
        self.assertEqual(C2Store(self.gd).read("beacons.tsv"), [], "拒收不入账")

    def test_register_unknown_cred_rejected_vault_placeholder_ok(self):
        with self.assertRaises(C2Error):
            beacon.register(self.gd, T0, self.iid, cred_ref="CRED-c2t-9999")
        bid, row = beacon.register(self.gd, ts(1), self.iid, cred_ref="{{vault:cred-1}}")
        self.assertTrue(bid.startswith("BCN-"), "id 前缀 BCN")
        self.assertEqual(row[C2_TABLES["beacons.tsv"].index("kind")], "register")

    def test_register_without_family_rejected(self):
        d, gd = boot_goal("G-nofam")
        self.addCleanup(d.cleanup)
        iid = add_intent(gd)
        with self.assertRaises(C2Error):
            beacon.register(gd, T0, iid)
        self.assertEqual(C2Store(gd).read("beacons.tsv"), [], "L3 族未批=零行落账")

    def test_heartbeat_projection_three_states(self):
        bid, _ = beacon.register(self.gd, ts(0), self.iid)
        beacon.heartbeat(self.gd, bid, ts(1))
        p = {b["id"]: b for b in beacon.projection(self.gd, ts(1, 30))}
        self.assertEqual(p[bid]["status"], "online", "lag=30s<=T 在线")
        self.assertEqual(p[bid]["last_hb"], ts(1))
        self.assertEqual(p[bid]["first_seen"], ts(0), "first_seen=register 时刻,心跳不改")
        self.assertEqual(p[bid]["heartbeats"], 1)
        p = {b["id"]: b for b in beacon.projection(self.gd, ts(2, 30))}
        self.assertEqual(p[bid]["status"], "stale", "T<lag=90s<=2T 陈旧")
        p = {b["id"]: b for b in beacon.projection(self.gd, ts(3, 30))}
        self.assertEqual(p[bid]["status"], "offline", "lag=150s>2T 离线=投影翻转")
        rows = C2Store(self.gd).read("beacons.tsv")
        self.assertEqual(len(rows), 2, "状态翻转零行改动(只增不改)")

    def test_heartbeat_unknown_beacon_rejected(self):
        with self.assertRaises(C2Error):
            beacon.heartbeat(self.gd, "BCN-c2t-9999", ts(1))
        self.assertEqual(len(C2Store(self.gd).read("beacons.tsv")), 0, "匿名心跳不入账")


class TestQueue(unittest.TestCase):
    """指令=append-only 行,拉取=行号游标(防重发防漏发,幂等重拉=空集)。"""

    def setUp(self):
        self.d, self.gd, self.iid, self.bid = boot_beacon()
        self.addCleanup(self.d.cleanup)

    def test_enqueue_unknown_beacon_rejected(self):
        with self.assertRaises(C2Error):
            queue.enqueue(self.gd, "BCN-c2t-9999", "id", ts(1))
        self.assertEqual(C2Store(self.gd).read("cmds.tsv"), [])

    def test_enqueue_empty_argv_rejected(self):
        with self.assertRaises(C2Error):
            queue.enqueue(self.gd, self.bid, "  ", ts(1))

    def test_enqueue_without_family_rejected(self):
        d, gd = boot_goal("G-q")
        self.addCleanup(d.cleanup)
        iid = add_intent(gd)
        grant_family(gd, "c2-beacon")
        bid, _ = beacon.register(gd, T0, iid)
        with self.assertRaises(C2Error):
            queue.enqueue(gd, bid, "id", ts(1))
        self.assertEqual(C2Store(gd).read("cmds.tsv"), [])

    def test_enqueue_anchors_active_family(self):
        cid, rowno = queue.enqueue(self.gd, self.bid, ["id", "-u"], ts(1))
        self.assertTrue(cid.startswith("CMD-"))
        self.assertEqual(rowno, 1)
        row = C2Store(self.gd).read("cmds.tsv")[0]
        self.assertTrue(row[4].startswith("FAM-"), "approval_ref 锚 L3 族行(c2-cmd)")
        self.assertEqual(row[2], "id -u", "list argv 空格连接串")

    def test_enqueue_max_cmds_boundary_stops(self):
        d, gd, iid, bid = boot_beacon("G-cap")
        self.addCleanup(d.cleanup)
        grant_family(gd, "c2-cmd", bounds="hosts=127.0.0.1;max-cmds=1")
        # boot_beacon 已放行过一个 c2-cmd 族(无上限);再放一个 max-cmds=1 的——
        # active() 取最新授批,故上限生效
        queue.enqueue(gd, bid, "id", ts(1))
        with self.assertRaises(C2Error):
            queue.enqueue(gd, bid, "whoami", ts(2))

    def test_pull_cursor_no_resend_no_miss_idempotent(self):
        bid2, _ = beacon.register(self.gd, ts(1), self.iid)
        queue.enqueue(self.gd, self.bid, "id", ts(1))
        queue.enqueue(self.gd, bid2, "whoami", ts(2))
        cmds, cursor = queue.pull(self.gd, self.bid, ts(3))
        self.assertEqual([c["id"] for c in cmds][0].startswith("CMD-"), True)
        self.assertEqual(len(cmds), 1, "只拉本 beacon 指令")
        self.assertEqual(cursor, 2, "游标=全表尾行号(跳过他 beacon 指令)")
        again, cursor2 = queue.pull(self.gd, self.bid, ts(4))
        self.assertEqual(again, [], "幂等重拉=空集")
        self.assertEqual(cursor2, 2, "空拉游标不动")
        queue.enqueue(self.gd, self.bid, "uname -a", ts(5))
        cmds3, _ = queue.pull(self.gd, self.bid, ts(6))
        self.assertEqual(len(cmds3), 1, "新指令行号>游标必达(不漏发)")
        self.assertEqual(cmds3[0]["argv"], "uname -a")
        self.assertEqual(cmds3[0]["rowno"], 3)
        self.assertEqual([c["id"] for c in queue.pending(self.gd, self.bid)], [],
                         "pending 只读面不动游标")

    def test_pull_unknown_beacon_empty(self):
        cmds, cursor = queue.pull(self.gd, "BCN-c2t-9999", ts(1))
        self.assertEqual((cmds, cursor), ([], 0))


class TestEcho(unittest.TestCase):
    """回显=证据化: 哈希锚+13 表单源写路径+大输出工件化+定长摘录。"""

    def setUp(self):
        self.d, self.gd, self.iid, self.bid = boot_beacon()
        self.addCleanup(self.d.cleanup)
        self.cid, _ = queue.enqueue(self.gd, self.bid, "whoami", ts(1))

    def test_submit_small_output_anchors_evidence(self):
        data = b"root\n"
        r = echo.submit(self.gd, self.cid, data, ts(2))
        self.assertEqual(r["digest"], hashlib.sha256(data).hexdigest(), "digest=sha256(字节)")
        self.assertFalse(r["large"])
        from ledger.schemas import TABLES as _T
        ai = _T["E-index.tsv"].index("artifact_path")
        rows = Session(self.gd).rows("E-index.tsv")
        self.assertEqual(rows[-1][ai], r["artifact_path"], "E-index 行工件路径=回显工件")
        tl = Session(self.gd).rows("timeline.tsv")
        self.assertTrue(any("add-evidence " in row[3] for row in tl), "走 add-evidence 同一写路径")
        er = echo.echoes_for(self.gd, self.cid)
        self.assertEqual(len(er), 1)
        self.assertEqual(er[0][3], r["digest"], "echoes 行锚 digest")

    def test_submit_large_output_artifactized(self):
        data = b"A" * (ECHO_ARTIFACT_THRESHOLD + 500)
        r = echo.submit(self.gd, self.cid, data, ts(2))
        self.assertTrue(r["large"], "超阈值=大输出")
        with open(os.path.join(self.gd, r["artifact_path"]), "rb") as f:
            self.assertEqual(f.read(), data, "全量只落工件")
        self.assertLessEqual(len(r["excerpt"]), EXCERPT_MAX, "账内只留定长摘录")
        self.assertEqual(C2Store(self.gd).read("echoes.tsv")[0][6], r["excerpt"])

    def test_submit_unknown_cmd_rejected(self):
        with self.assertRaises(C2Error):
            echo.submit(self.gd, "CMD-c2t-9999", b"x", ts(2))
        self.assertEqual(C2Store(self.gd).read("echoes.tsv"), [])

    def test_submit_non_bytes_rejected(self):
        with self.assertRaises(C2Error):
            echo.submit(self.gd, self.cid, "root", ts(2))

    def test_submit_requires_family(self):
        d, gd = boot_goal("G-echo")
        self.addCleanup(d.cleanup)
        iid = add_intent(gd)
        grant_family(gd, "c2-beacon")
        grant_family(gd, "c2-cmd")
        bid, _ = beacon.register(gd, T0, iid)
        cid, _ = queue.enqueue(gd, bid, "id", ts(1))
        with self.assertRaises(C2Error):
            echo.submit(gd, cid, b"root", ts(2))
        self.assertEqual(C2Store(gd).read("echoes.tsv"), [])


class TestFamilies(unittest.TestCase):
    """L3 预授权审批族: 批一次放一族,bounds+expire,出界即停,撤批即死。"""

    def setUp(self):
        self.d, self.gd = boot_goal()
        self.addCleanup(self.d.cleanup)

    def test_grant_unknown_family_rejected(self):
        with self.assertRaises(C2Error):
            families.grant(self.gd, "c2-nope", "", "op", "2026-10-18T00:00:00Z",
                           "2026-10-19T00:00:00Z", T0)

    def test_grant_bad_window_rejected(self):
        with self.assertRaises(C2Error):
            families.grant(self.gd, "c2-cmd", "", "op", "2026-10-19T00:00:00Z",
                           "2026-10-18T00:00:00Z", T0)

    def test_grant_bad_bounds_rejected(self):
        with self.assertRaises(C2Error):
            families.grant(self.gd, "c2-cmd", "host=127.0.0.1", "op",
                           "2026-10-18T00:00:00Z", "2026-10-19T00:00:00Z", T0)
        with self.assertRaises(C2Error):
            families.grant(self.gd, "c2-cmd", "max-cmds=zero", "op",
                           "2026-10-18T00:00:00Z", "2026-10-19T00:00:00Z", T0)

    def test_require_ok_returns_active_row(self):
        fid, row = families.grant(self.gd, "c2-cmd", "hosts=127.0.0.1", "op",
                                  "2026-10-18T00:00:00Z", "2026-10-19T00:00:00Z", T0)
        got = families.require(self.gd, "c2-cmd", ts(1))
        self.assertEqual(got[0], fid)
        self.assertEqual(got[3], "grant", "decision=grant")

    def test_require_ungranted_fail_closed(self):
        with self.assertRaises(C2Error):
            families.require(self.gd, "c2-cmd", ts(1))

    def test_require_expired_rejected(self):
        families.grant(self.gd, "c2-cmd", "", "op", "2026-10-18T00:00:00Z",
                       "2026-10-18T09:00:00Z", T0)
        with self.assertRaises(C2Error):
            families.require(self.gd, "c2-cmd", ts(61))

    def test_revoke_kills_family(self):
        fid, _ = families.grant(self.gd, "c2-cmd", "", "op",
                                "2026-10-18T00:00:00Z", "2026-10-19T00:00:00Z", T0)
        families.revoke(self.gd, fid, ts(1))
        with self.assertRaises(C2Error):
            families.require(self.gd, "c2-cmd", ts(2))
        rows = C2Store(self.gd).read("families.tsv")
        self.assertEqual(len(rows), 2, "撤批=追加行,不改历史")

    def test_revoke_unknown_id_rejected(self):
        with self.assertRaises(C2Error):
            families.revoke(self.gd, "FAM-c2t-9999", ts(1))

    def test_bounds_parse_and_hosts(self):
        b = families.parse_bounds("hosts=127.0.0.1,::1;max-cmds=5")
        self.assertEqual(b, {"hosts": ["127.0.0.1", "::1"], "max-cmds": 5})
        self.assertEqual(families.parse_bounds(""), {})


if __name__ == "__main__":
    unittest.main()
