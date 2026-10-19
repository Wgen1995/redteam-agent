# -*- coding: utf-8 -*-
"""T12 发现页读面: 列表过滤/详情证据袋+复放史/复验触发(桥)/零副作用。"""
import os
import shutil
import tempfile
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from server.readface.main import app
from tests.readface.test_chat_stream import _mk_goal, _mk_runner

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURE = os.path.join(REPO_ROOT, "tests", "fixtures", "G-r18")


class _Syn:
    def __init__(self):
        home = tempfile.mkdtemp(prefix="readface-t12-home-")
        b1 = os.path.join(home, "battles", "battle-1")
        os.makedirs(b1)
        shutil.copytree(FIXTURE, os.path.join(b1, "G-r18"))
        _mk_runner(b1)
        b2 = os.path.join(home, "battles", "battle-2")
        _mk_goal(
            os.path.join(b2, "G-1"),
            [("2026-10-14T10:00:00Z", "op", "P3", "b2 row", "")],
            {"goals.tsv": [{"id": "G-s-2", "target": "t2"}],
             "findings.tsv": [
                 {"id": "FD-s-9", "title": "no ev", "confidence": "C2",
                  "affected_asset_id": "AST-s-1", "status": "active"}]})
        _mk_runner(b2)
        self.home = home


class FindingsListTests(unittest.TestCase):
    def setUp(self):
        self.syn = _Syn()
        self.patcher = mock.patch.dict(os.environ, {"TANYIN_HOME": self.syn.home})
        self.patcher.start()
        self.client = TestClient(app)
        self.addCleanup(self.patcher.stop)
        self.addCleanup(shutil.rmtree, self.syn.home, True)

    def test_all_shape_and_sort(self):
        r = self.client.get("/api/findings")
        self.assertEqual(r.status_code, 200)
        rows = r.json()
        self.assertTrue(len(rows) >= 77)  # G-r18 76 + FD-s-9
        need = {"id", "title", "severity", "where", "verified",
                "replay_state", "evidence", "battle", "badge", "ts"}
        for row in rows:
            self.assertTrue(need <= set(row))
        ts_list = [row["ts"] or "" for row in rows]
        self.assertEqual(ts_list, sorted(ts_list, reverse=True))

    def test_filter_battle(self):
        rows = self.client.get("/api/findings", params={"battle": "battle-1"}).json()
        self.assertTrue(rows)
        self.assertTrue(all(r["id"].startswith("FD-r18-") for r in rows))
        self.assertEqual(
            self.client.get("/api/findings", params={"battle": "nope"}).json(), [])

    def test_filter_severity_and_state(self):
        rows = self.client.get("/api/findings", params={"severity": "C1"}).json()
        self.assertTrue(rows)
        self.assertTrue(all(r["severity"] == "C1" for r in rows))
        ver = self.client.get("/api/findings", params={"state": "verified"}).json()
        self.assertTrue(all(r["verified"] for r in ver))
        pend = self.client.get("/api/findings", params={"state": "pending"}).json()
        self.assertTrue(pend and all(not r["verified"] for r in pend))
        self.assertIn("FD-r18-0076", [r["id"] for r in pend])

    def test_read_zero_side_effect(self):
        before = {}
        for root, _d, files in os.walk(self.syn.home):
            for fn in files:
                p = os.path.join(root, fn)
                before[p] = (os.stat(p).st_mtime, os.stat(p).st_size)
        self.client.get("/api/findings")
        self.client.get("/api/findings/FD-r18-0075")
        for p, (mt, sz) in before.items():
            self.assertEqual((os.stat(p).st_mtime, os.stat(p).st_size), (mt, sz),
                             "读端点不得改任何文件: %s" % p)


class FindingsDetailTests(unittest.TestCase):
    def setUp(self):
        self.syn = _Syn()
        self.patcher = mock.patch.dict(os.environ, {"TANYIN_HOME": self.syn.home})
        self.patcher.start()
        self.client = TestClient(app)
        self.addCleanup(self.patcher.stop)
        self.addCleanup(shutil.rmtree, self.syn.home, True)

    def test_detail_with_evidence(self):
        r = self.client.get("/api/findings/FD-r18-0075")
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertTrue(d["evidence"])
        self.assertTrue(all(x.startswith("EV-") for x in d["evidence"]))
        self.assertIn("evidence_detail", d)
        self.assertIn("replay_history", d)

    def test_detail_unknown_404(self):
        self.assertEqual(
            self.client.get("/api/findings/FD-x-none").status_code, 404)


class ReverifyTests(unittest.TestCase):
    def setUp(self):
        self.syn = _Syn()
        self.patcher = mock.patch.dict(os.environ, {"TANYIN_HOME": self.syn.home})
        self.patcher.start()
        self.client = TestClient(app)
        self.addCleanup(self.patcher.stop)
        self.addCleanup(shutil.rmtree, self.syn.home, True)

    def test_unknown_404(self):
        self.assertEqual(
            self.client.post("/api/findings/FD-x-none/reverify").status_code, 404)

    def test_no_evidence_422(self):
        r = self.client.post("/api/findings/FD-s-9/reverify")
        self.assertEqual(r.status_code, 422)
        self.assertIn("无绑定证据卡", r.json()["error"])

    def test_bridge_ok_passthrough(self):
        canned = {"ok": True, "cmd": "reverify", "battle": "battle-1",
                  "finding": "FD-r18-0075",
                  "results": [{"ev": "EV-r18-0041", "verdict": "reproduced",
                               "rc": 0, "note": ""}],
                  "state_note": "回写走验证官 settle 门"}
        import json as _json
        import server.readface.routers.findings as mod
        with mock.patch.object(mod, "_bridge_reverify") as br:
            m = mock.Mock(returncode=0)
            m.stdout = "前置行\n" + _json.dumps(canned)
            br.return_value = m
            r = self.client.post("/api/findings/FD-r18-0075/reverify")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["results"][0]["verdict"], "reproduced")

    def test_bridge_fail_502(self):
        import server.readface.routers.findings as mod
        with mock.patch.object(mod, "_bridge_reverify") as br:
            br.side_effect = RuntimeError("boom")
            r = self.client.post("/api/findings/FD-r18-0075/reverify")
        self.assertEqual(r.status_code, 502)


if __name__ == "__main__":
    unittest.main()
