# -*- coding: utf-8 -*-
"""T4 读面总览测试(测试先行:先跑红,再实现跑绿)。

覆盖两用例(裁决: 本任务兼建 routers/overview.py):
- G-r18 形状: GET /api/overview → 恰三键
  {active_battles, soldiers_running, pending_approvals},数值=
  合成 battles 根内「执行中」仗(引擎状态机单源判读)的当代 goal 目录上:
  soldiers_now 非终态计数(终态={done,rejected},写侧链前置门同律)+
  approvals_pending 长度;非执行中仗(已完跑)的兵/待审不入数。
- 零 side effect: 打一遍端点,合成 battles 树(含 G-r18 夹具副本)
  字节+mtime 纹丝不动(纯读铁律)。

合成根(TANYIN_HOME 注入,不碰真实 ~/.tanyin):
- battle-1 = G-r18 夹具副本 + runner 已点火未完跑(LAUNCH 无 DONE)→执行中;
- battle-2 = 微型 goal(1 active+1 done+1 rejected 意图;1 条 revert_cmd 待审)
  + runner 已点火未完跑→执行中;
- battle-3 = 微型 goal(2 active 意图)+ runner 已完跑(DONE final_rc=0)
  →非执行中,其兵不计。
期望: active=2, soldiers=6(G-r18 全 pending)+1(battle-2 仅 active),
approvals=1(battle-2)。

运行(仓库根): PYTHONPATH=cli python3 -m unittest tests.readface.test_overview -v
"""
import hashlib
import os
import shutil
import tempfile
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from server.readface.main import app

from ledger import core as ledger_core
from ledger import timeline as ledger_timeline
from ledger.schemas import TABLES

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
FIXTURE = os.path.join(REPO_ROOT, "tests", "fixtures", "G-r18")


def _chain(spec):
    """[(ts,actor,phase,event,revert_cmd)...] → 引擎真实接链的 8 列行。"""
    rows = []
    for ts, actor, phase, event, revert in spec:
        row, _ = ledger_timeline.chained_row(rows, ts, actor, phase, event, revert)
        rows.append(row)
    return rows


def _mk_goal(gd, tl_spec, tables=None):
    """微型 goal: 接链 timeline+若干净表(引擎 write_tsv 落盘,缺列补空)。"""
    os.makedirs(gd)
    ledger_core.write_tsv(os.path.join(gd, "timeline.tsv"), _chain(tl_spec))
    for tname, dict_rows in (tables or {}).items():
        cols = TABLES[tname]
        ledger_core.write_tsv(
            os.path.join(gd, tname),
            [[d.get(c, "") for c in cols] for d in dict_rows])


def _mk_runner(battle_dir, done=False):
    """runner 生命周期行: 已点火未完跑(LAUNCH 无 DONE)或已完跑(DONE)。"""
    lines = ["2026-10-14T09:00:00Z\tBOOT\tup",
             "2026-10-14T09:00:05Z\tLAUNCH\topencode"]
    if done:
        lines.append("2026-10-14T10:00:00Z\tDONE\tfinal_rc=0")
    with open(os.path.join(battle_dir, "opencode-run.log.runner.tsv"),
              "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


class OverviewTests(unittest.TestCase):
    """/api/overview: 三数形状+读法自释的判读。"""

    def setUp(self):
        home = tempfile.mkdtemp(prefix="readface-t4-home-")
        self.addCleanup(shutil.rmtree, home, True)
        # battle-1: G-r18 夹具副本,已点火未完跑 → 执行中(6 pending 兵/0 待审)
        b1 = os.path.join(home, "battles", "battle-1")
        os.makedirs(b1)
        shutil.copytree(FIXTURE, os.path.join(b1, "G-r18"))
        _mk_runner(b1)
        # battle-2: 1 active+1 done+1 rejected 意图;1 条 revert_cmd 待审 → 执行中
        b2 = os.path.join(home, "battles", "battle-2")
        _mk_goal(
            os.path.join(b2, "G-1"),
            [("2026-10-14T10:00:00Z", "op", "P3",
              "http-get http://x/a", "rb-1")],
            {"goals.tsv": [{"id": "G-s-2", "target": "demo-target"}],
             "intents.tsv": [
                 {"id": "INT-s-1", "title": "live-scan", "status": "active",
                  "kind": "recon", "budget_share": "100;2;1"},
                 {"id": "INT-s-2", "title": "finished", "status": "done",
                  "kind": "recon"},
                 {"id": "INT-s-3", "title": "refused", "status": "rejected",
                  "kind": "recon"}]})
        _mk_runner(b2)
        # battle-3: 2 active 意图但已完跑(DONE)→非执行中,兵不计
        b3 = os.path.join(home, "battles", "battle-3")
        _mk_goal(
            os.path.join(b3, "G-1"),
            [("2026-10-14T11:00:00Z", "op", "P3", "note row", "")],
            {"goals.tsv": [{"id": "G-s-3", "target": "done-target"}],
             "intents.tsv": [
                 {"id": "INT-s-4", "title": "a", "status": "active",
                  "kind": "recon"},
                 {"id": "INT-s-5", "title": "b", "status": "active",
                  "kind": "recon"}]})
        _mk_runner(b3, done=True)
        self.home = home
        self.client = TestClient(app)

    def test_g18_shape_three_ints(self):
        with mock.patch.dict(os.environ, {"TANYIN_HOME": self.home}):
            resp = self.client.get("/api/overview")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {
            "active_battles": 2,       # battle-1/2 执行中;battle-3 已完跑
            "soldiers_running": 7,     # 6(G-r18 pending)+1(battle-2 active)
            "pending_approvals": 1,    # battle-2 revert_cmd 待审
        })


class ZeroSideEffectTests(unittest.TestCase):
    """纯读铁律: 端点打一遍,合成 battles 树字节+mtime 纹丝不动。"""

    def _snapshot(self, root):
        snap = {}
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                p = os.path.join(dirpath, name)
                st = os.stat(p)
                with open(p, "rb") as f:
                    digest = hashlib.md5(f.read()).hexdigest()
                snap[p] = (st.st_size, st.st_mtime_ns, digest)
        return snap

    def test_overview_leaves_battles_tree_untouched(self):
        home = tempfile.mkdtemp(prefix="readface-t4-snap-")
        self.addCleanup(shutil.rmtree, home, True)
        b1 = os.path.join(home, "battles", "battle-1")
        os.makedirs(b1)
        shutil.copytree(FIXTURE, os.path.join(b1, "G-r18"))
        _mk_runner(b1)
        before = self._snapshot(home)
        client = TestClient(app)
        with mock.patch.dict(os.environ, {"TANYIN_HOME": home}):
            resp = client.get("/api/overview")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._snapshot(home), before)


if __name__ == "__main__":
    unittest.main()
