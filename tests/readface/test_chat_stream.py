# -*- coding: utf-8 -*-
"""T5 指挥流读面测试(测试先行:先跑红,再实现跑绿)。

覆盖(件A 两端点,合成 battles 根+G-r18 夹具):
- stream 合并序: battles 根枚举全部仗目录(执行中/已完跑都入流——
  指挥台时间线不分仗态),每仗当代 goal(battle-N/G-* 末代,tasks_view
  单源)timeline_tail 各取,按 (ts,key) 全局新→旧归并;每行带 battle
  标识+badge(battle 目录名 sha256 派生稳定色相)。
- 游标翻页: next_cursor=base64(各仗页内末 key 映射);逐页走全链,
  并集=三仗全部行,零重复零遗漏,跨页 ts 单调不增(无重无漏走链)。
- 徽标色稳定: 同仗两次请求同色;与 sha256 派生式一致;异仗异色;
  warboard 与 stream 同源同色。
- 空根零行不造假: battles 根不存在/存在但空 → rows=[] next_cursor=None。
- 坏游标: 非 base64/非映射 JSON/悬空 key(不在链上)→400。
- limit 校验: 0/负 → 422(FastAPI ge=1)。
- warboard: {soldiers,findings_latest,approvals} 三格皆注 battle;
  findings 每仗取前 5(G-r18 夹具 110 行只出 5);待审=引擎同源 pending。
- 纯读零 side effect: stream 首页+翻页+warboard 打一遍,合成 battles
  树字节+mtime 纹丝不动。

运行(仓库根): PYTHONPATH=cli python3 -m unittest tests.readface.test_chat_stream -v
"""
import base64
import hashlib
import json
import os
import re
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

_BADGE_RE = re.compile(r"^hsl\((\d+), (\d+)%, (\d+)%\)$")


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


def _badge_of(battle):
    """徽标色派生式(与实现同契约): sha256(目录名)前 8 hex → 色相。"""
    hue = int(hashlib.sha256(battle.encode("utf-8")).hexdigest()[:8], 16) % 360
    return "hsl(%d, 70%%, 60%%)" % hue


class _SyntheticHome(object):
    """合成 battles 根(TANYIN_HOME 注入,不碰真实 ~/.tanyin)。

    - battle-1 = G-r18 夹具副本(709 行 timeline/110 行 findings)+
      runner 已点火未完跑 → 执行中;
    - battle-2 = 微型 goal: 4 行 timeline 跨 G-r18 首尾(07:30 最老全局/
      14:30 最新全局)+1 active+1 done 意图+3 行 findings+1 条 revert_cmd
      待审;runner 已点火未完跑 → 执行中;
    - battle-3 = 微型 goal 2 行(09:30/09:45,落 G-r18 中段)+runner 已完跑
      (DONE)→ 已完跑仗照样入流(全部仗枚举,不分仗态)。
    """

    def __init__(self):
        home = tempfile.mkdtemp(prefix="readface-t5-home-")
        b1 = os.path.join(home, "battles", "battle-1")
        os.makedirs(b1)
        shutil.copytree(FIXTURE, os.path.join(b1, "G-r18"))
        _mk_runner(b1)
        b2 = os.path.join(home, "battles", "battle-2")
        _mk_goal(
            os.path.join(b2, "G-1"),
            [("2026-10-14T07:30:00Z", "op", "P3", "early note", ""),
             ("2026-10-14T10:00:00Z", "op", "P3", "mid note b2", ""),
             ("2026-10-14T12:00:00Z", "op", "P3", "http-get http://x/a", "rb-1"),
             ("2026-10-14T14:30:00Z", "op", "P3", "late scan b2", "")],
            {"goals.tsv": [{"id": "G-s-2", "target": "demo-target"}],
             "intents.tsv": [
                 {"id": "INT-s-1", "title": "live-scan", "status": "active",
                  "kind": "recon", "budget_share": "100;2;1"},
                 {"id": "INT-s-2", "title": "finished", "status": "done",
                  "kind": "recon"}],
             "findings.tsv": [
                 {"id": "FD-s-1", "title": "f one", "confidence": "高",
                  "affected_asset_id": "AST-s-1", "status": "active"},
                 {"id": "FD-s-2", "title": "f two", "confidence": "中",
                  "affected_asset_id": "AST-s-2", "status": "active"},
                 {"id": "FD-s-3", "title": "f three", "confidence": "低",
                  "affected_asset_id": "", "status": "active"}]})
        _mk_runner(b2)
        b3 = os.path.join(home, "battles", "battle-3")
        _mk_goal(
            os.path.join(b3, "G-1"),
            [("2026-10-14T09:30:00Z", "op", "P3", "b3 first", ""),
             ("2026-10-14T09:45:00Z", "op", "P3", "b3 second", "")],
            {"goals.tsv": [{"id": "G-s-3", "target": "done-target"}]})
        _mk_runner(b3, done=True)
        self.home = home
        self.goals = {
            "battle-1": os.path.join(home, "battles", "battle-1", "G-r18"),
            "battle-2": os.path.join(home, "battles", "battle-2", "G-1"),
            "battle-3": os.path.join(home, "battles", "battle-3", "G-1"),
        }

    def all_keys(self):
        """三仗当代 goal 全量 key 集(对照并集用,ledger_reader 单源)。"""
        import server.readface.ledger_reader as lr
        keys = set()
        for gd in self.goals.values():
            keys.update(r["key"] for r in lr.timeline_tail(gd, limit=10 ** 6))
        return keys

    def cleanup(self):
        shutil.rmtree(self.home, True)


class StreamTests(unittest.TestCase):
    """/api/chat/stream: 跨仗合并时间线+游标反向分页。"""

    def setUp(self):
        self.syn = _SyntheticHome()
        self.addCleanup(self.syn.cleanup)
        self.client = TestClient(app)

    def _get(self, **params):
        with mock.patch.dict(os.environ, {"TANYIN_HOME": self.syn.home}):
            return self.client.get("/api/chat/stream", params=params)

    def test_merged_order_and_row_shape(self):
        resp = self._get(limit=10)
        self.assertEqual(resp.status_code, 200)
        doc = resp.json()
        self.assertEqual(set(doc), {"rows", "next_cursor"})
        rows = doc["rows"]
        self.assertEqual(len(rows), 10)
        for it in rows:
            self.assertEqual(set(it),
                             {"key", "ts", "kind", "detail", "battle", "badge"})
            self.assertIn(it["battle"], self.syn.goals)
            m = _BADGE_RE.match(it["badge"])
            self.assertIsNotNone(m, "badge 须为 hsl 形: %r" % it["badge"])
        # 全局新→旧: 相邻 ts 不增
        for a, b in zip(rows, rows[1:]):
            self.assertGreaterEqual(a["ts"], b["ts"])
        # 首行=battle-2 14:30(全局最新),末行不在 battle-2 07:30(才取 10 行)
        self.assertEqual(rows[0]["battle"], "battle-2")
        self.assertEqual(rows[0]["detail"], "late scan b2")
        # 中段必须混仗(battle-1 G-r18 中段行与 battle-3 09:30/09:45 交错)
        battles_seen = {it["battle"] for it in rows}
        self.assertIn("battle-1", battles_seen)

    def test_cursor_walk_full_chain_no_dup_no_gap(self):
        seen = []
        cursor = None
        for _ in range(300):                      # 715 行/页 7 → ≤103 页
            resp = self._get(limit=7, **({"before_key": cursor} if cursor else {}))
            self.assertEqual(resp.status_code, 200)
            doc = resp.json()
            seen.extend(doc["rows"])
            cursor = doc["next_cursor"]
            if cursor is None:
                break
        # 无重
        keys = [r["key"] for r in seen]
        self.assertEqual(len(keys), len(set(keys)))
        # 无漏: 并集=三仗当代 goal 全量 key
        self.assertEqual(set(keys), self.syn.all_keys())
        self.assertEqual(len(keys), 709 + 4 + 2)
        # 跨页全局新→旧(无重无漏走链)
        for a, b in zip(seen, seen[1:]):
            self.assertGreaterEqual(a["ts"], b["ts"])
        # 最老行=battle-2 07:30;最老一页收尾后游标归 None
        self.assertEqual(seen[-1]["detail"], "early note")

    def test_cursor_is_base64_battle_key_map(self):
        resp = self._get(limit=3)
        cursor = resp.json()["next_cursor"]
        self.assertTrue(cursor)
        raw = base64.b64decode(cursor.encode("ascii"))
        mapping = json.loads(raw.decode("utf-8"))
        self.assertIsInstance(mapping, dict)
        self.assertTrue(mapping)
        for battle, key in mapping.items():
            self.assertIn(battle, self.syn.goals)
            self.assertRegex(key, r"^[0-9a-f]{64}$")
        # 映射里的 key 须真在页内该仗最旧行
        rows = resp.json()["rows"]
        for battle, key in mapping.items():
            last = [r for r in rows if r["battle"] == battle][-1]
            self.assertEqual(last["key"], key)

    def test_badge_stable_and_derived(self):
        r1 = self._get(limit=5).json()["rows"]
        r2 = self._get(limit=5).json()["rows"]
        for a, b in zip(r1, r2):
            self.assertEqual(a["badge"], b["badge"])        # 同仗同色
            self.assertEqual(a["badge"], _badge_of(a["battle"]))  # 派生式
        colors = {_badge_of(b) for b in self.syn.goals}
        self.assertEqual(len(colors), 3)                    # 异仗异色(284/3/172)

    def test_empty_root_zero_rows_no_fabrication(self):
        empty = tempfile.mkdtemp(prefix="readface-t5-empty-")
        self.addCleanup(shutil.rmtree, empty, True)
        for home in (empty, os.path.join(empty, "battles")):
            os.makedirs(home, exist_ok=True)
            with mock.patch.dict(os.environ, {"TANYIN_HOME": home}):
                resp = self.client.get("/api/chat/stream")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json(), {"rows": [], "next_cursor": None})

    def test_bad_cursor_rejected_400(self):
        cases = ["!!!not-base64!!!",
                 base64.b64encode(b"[1,2]").decode("ascii"),
                 base64.b64encode(json.dumps({"battle-1": "0" * 64}).encode())
                 .decode("ascii")]
        for bad in cases:
            resp = self._get(limit=5, before_key=bad)
            self.assertEqual(resp.status_code, 400, "坏游标须 400: %r" % bad)
            self.assertIn("error", resp.json())

    def test_limit_validation(self):
        for bad in ("0", "-3", "abc"):
            resp = self._get(limit=bad)
            self.assertEqual(resp.status_code, 422, "limit=%s 须 422" % bad)


class WarboardTests(unittest.TestCase):
    """/api/chat/warboard: 三格各仗合并,皆注 battle。"""

    def setUp(self):
        self.syn = _SyntheticHome()
        self.addCleanup(self.syn.cleanup)
        self.client = TestClient(app)

    def _get(self):
        with mock.patch.dict(os.environ, {"TANYIN_HOME": self.syn.home}):
            return self.client.get("/api/chat/warboard")

    def test_shape_and_battle_annotation(self):
        resp = self._get()
        self.assertEqual(resp.status_code, 200)
        doc = resp.json()
        self.assertEqual(set(doc), {"soldiers", "findings_latest", "approvals"})
        for s in doc["soldiers"]:
            self.assertIn("battle", s)
            self.assertIn("badge", s)
            self.assertIn(s["battle"], self.syn.goals)
        # battle-2 两意图都在列(soldiers_now 各仗合并原样,状态透传不筛)
        b2 = {s["intent"]: s for s in doc["soldiers"] if s["battle"] == "battle-2"}
        self.assertEqual(set(b2), {"live-scan", "finished"})
        self.assertEqual(b2["live-scan"]["status"], "active")
        self.assertEqual(b2["finished"]["status"], "done")
        # findings 每仗前 5: G-r18 夹具 110 行只出 5;battle-2 全 3 行
        f1 = [f for f in doc["findings_latest"] if f["battle"] == "battle-1"]
        f2 = [f for f in doc["findings_latest"] if f["battle"] == "battle-2"]
        self.assertEqual(len(f1), 5)
        self.assertEqual({f["id"] for f in f2}, {"FD-s-1", "FD-s-2", "FD-s-3"})
        # 待审: battle-2 的 revert_cmd 行(引擎 cleanup 同源)
        self.assertEqual(len(doc["approvals"]), 1)
        ap = doc["approvals"][0]
        self.assertEqual(ap["battle"], "battle-2")
        self.assertEqual(ap["event"], "http-get http://x/a")
        self.assertRegex(ap["id"], r"^[0-9a-f]{64}$")
        self.assertIn("timeout_policy", ap)

    def test_badge_same_source_as_stream(self):
        board = self._get().json()
        with mock.patch.dict(os.environ, {"TANYIN_HOME": self.syn.home}):
            stream = self.client.get("/api/chat/stream", params={"limit": 50})
        stream_badge = {r["battle"]: r["badge"]
                        for r in stream.json()["rows"]}
        for item in board["soldiers"] + board["findings_latest"] +                 board["approvals"]:
            self.assertEqual(item["badge"], _badge_of(item["battle"]))
            if item["battle"] in stream_badge:
                self.assertEqual(item["badge"],
                                 stream_badge[item["battle"]])


class ZeroSideEffectTests(unittest.TestCase):
    """纯读铁律: stream 首页+翻页+warboard 打一遍,树纹丝不动。"""

    def _snapshot(self, root):
        snap = {}
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                p = os.path.join(dirpath, name)
                st = os.stat(p)
                with open(p, "rb") as f:
                    snap[p] = (st.st_size, st.st_mtime_ns,
                               hashlib.md5(f.read()).hexdigest())
        return snap

    def test_chat_endpoints_leave_battles_tree_untouched(self):
        syn = _SyntheticHome()
        self.addCleanup(syn.cleanup)
        before = self._snapshot(syn.home)
        client = TestClient(app)
        with mock.patch.dict(os.environ, {"TANYIN_HOME": syn.home}):
            resp = client.get("/api/chat/stream", params={"limit": 9})
            cursor = resp.json()["next_cursor"]
            if cursor:
                client.get("/api/chat/stream",
                           params={"limit": 9, "before_key": cursor})
            client.get("/api/chat/warboard")
        self.assertEqual(self._snapshot(syn.home), before)


if __name__ == "__main__":
    unittest.main()
