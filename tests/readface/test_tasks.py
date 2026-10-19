# -*- coding: utf-8 -*-
"""T11 任务列表+详情·会话签读面测试(测试先行:先跑红,再实现跑绿)。

覆盖(件A 三端点,合成 battles 根+G-r18 夹具):
- 列表形状: battles 根枚举(tasks_view 单源,同 overview 口径不分仗态),
  每仗 {id,name,status,status_detail,running,badge,goal,soldiers_n,
  findings_n,latest_ts}——status=tasks_view 界面七态标签原样透传
  (执行中/复测/草稿…,「执行中/已完跑」口径单源零第二份);running=
  标签==执行中(overview._RUNNING_LABEL 同词);badge=sha256 派生色相
  (stream/warboard 同源);soldiers_n/findings_n=ledger_reader
  soldiers_now/findings_list 计数如实(不筛态);latest_ts=当代 goal
  timeline 全量最大 ts(无 goal=None 不造假)。
- 详情分组: 列表字段+objective(goals 简述透传)+sessions=该仗 timeline
  按战士/意图分组——线索序: actor warrior:X > 事件 warrior=/steer
  target=(warrior-start/-heartbeat/-stop/steer) > intent=INT-x >
  add-intent INT-x > 其余归 deck(战役本级);每组 {session_key,label,
  rows_n,first_ts,last_ts};组序 last_ts 新→旧(同 ts 以 session_key
  定序);分组并集=该仗全部行(无重无漏)。
- 组流翻页: GET /api/tasks/{id}/sessions/{key}?before_key= 行形状同 T5
  ({key,ts,kind,detail,battle,badge}+badge 同源)+组内 (ts,key) 新→旧
  +key 游标反向分页走全链无重无漏;steer 行落战士组(留痕可见)。
- 未知面: 未知仗 404(详情+组流);仗在而会话组不在 404;坏/跨组游标 400;
  limit 0/负/坏 → 422(FastAPI 校验)。
- 纯读零 side effect: 三端点+翻页+坏游标打一遍,合成树字节+mtime
  纹丝不动。

运行(仓库根): PYTHONPATH=cli python3 -m unittest tests.readface.test_tasks -v
"""
import hashlib
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

    - battle-1 = G-r18 夹具副本(709 行 timeline/6 意图/76 发现)+runner
      已点火未完跑 → 执行中;
    - battle-2 = 微型 goal 4 行 timeline+2 意图+3 发现+runner 未完跑
      → 执行中;
    - battle-3 = 微型 goal 2 行+runner 已完跑(DONE rc=0)→ 复测
      (执行完跑·待复测——已完跑口径照入列表不分态);
    - battle-4 = 战士会话仗: warrior-start/heartbeat(warrior=w1
      intent=INT-4-1)/战士行 http-get/steer target=w1/warrior-stop +
      add-goal/deck-halt 归 deck;runner 未完跑 → 执行中;
    - battle-5 = 空目录无代 goal → 草稿(零计数零 latest 如实)。
    """

    def __init__(self):
        home = tempfile.mkdtemp(prefix="readface-t11-home-")
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
        b4 = os.path.join(home, "battles", "battle-4")
        _mk_goal(
            os.path.join(b4, "G-1"),
            [("2026-10-14T09:00:00Z", "op", "P0",
              "add-goal G-1 warrior-battle demo", ""),
             ("2026-10-14T09:00:05Z", "runner", "P3",
              "warrior-start battle=battle-4 warrior=w1 pid=101 model=strong", ""),
             ("2026-10-14T09:00:10Z", "warrior:w1", "P3",
              "warrior-heartbeat warrior=w1 intent=INT-4-1", ""),
             ("2026-10-14T09:00:20Z", "warrior:w1", "P3",
              "http-get http://10.2.0.7/", ""),
             ("2026-10-14T09:00:30Z", "总控", "P3",
              "warrior-steer target=w1 text=skip 10.2.0.9 focus 10.2.0.7", ""),
             ("2026-10-14T09:00:40Z", "总控", "P3",
              "warrior-stop warrior=w1 reason=demo halt", ""),
             ("2026-10-14T09:00:45Z", "总控", "P-lifecycle",
              "deck-halt battle=battle-4 reason=demo halt", "")],
            {"goals.tsv": [{"id": "G-s-4", "target": "warrior-target",
                            "objective": "会话签分组演示仗"}],
             "intents.tsv": [
                 {"id": "INT-4-1", "title": "live-scan", "status": "active",
                  "kind": "recon", "budget_share": "100;2;1"}]})
        _mk_runner(b4)
        os.makedirs(os.path.join(home, "battles", "battle-5"))
        self.home = home
        self.goals = {
            "battle-1": os.path.join(home, "battles", "battle-1", "G-r18"),
            "battle-2": os.path.join(home, "battles", "battle-2", "G-1"),
            "battle-3": os.path.join(home, "battles", "battle-3", "G-1"),
            "battle-4": os.path.join(home, "battles", "battle-4", "G-1"),
        }

    def cleanup(self):
        shutil.rmtree(self.home, True)


class _Base(unittest.TestCase):
    def setUp(self):
        self.syn = _SyntheticHome()
        self.addCleanup(self.syn.cleanup)
        self.client = TestClient(app)

    def _get(self, path, **params):
        with mock.patch.dict(os.environ, {"TANYIN_HOME": self.syn.home}):
            return self.client.get(path, params=params)


class TasksListTests(_Base):
    """/api/tasks: 仗列表(battles 根枚举,单源同 overview 不分仗态)。"""

    def test_shape_and_status_criteria(self):
        resp = self._get("/api/tasks")
        self.assertEqual(resp.status_code, 200)
        doc = resp.json()
        self.assertEqual(set(doc), {"battles"})
        rows = doc["battles"]
        self.assertEqual([r["id"] for r in rows],
                         ["battle-1", "battle-2", "battle-3",
                          "battle-4", "battle-5"])
        for it in rows:
            self.assertEqual(
                set(it),
                {"id", "name", "status", "status_detail", "running",
                 "badge", "goal", "soldiers_n", "findings_n", "latest_ts"})
            self.assertIsInstance(it["running"], bool)
            self.assertIsInstance(it["soldiers_n"], int)
            self.assertIsInstance(it["findings_n"], int)
            self.assertIsNotNone(_BADGE_RE.match(it["badge"]))
        by = {r["id"]: r for r in rows}
        # 状态=tasks_view 标签单源透传(执行中/复测/草稿),running=执行中口径
        self.assertEqual(by["battle-1"]["status"], "执行中")
        self.assertTrue(by["battle-1"]["running"])
        self.assertEqual(by["battle-2"]["status"], "执行中")
        self.assertTrue(by["battle-2"]["running"])
        self.assertEqual(by["battle-3"]["status"], "复测")   # 已完跑照入列
        self.assertFalse(by["battle-3"]["running"])
        self.assertEqual(by["battle-3"]["status_detail"], "执行完跑 · 待复测")
        self.assertEqual(by["battle-5"]["status"], "草稿")
        self.assertFalse(by["battle-5"]["running"])

    def test_counts_and_latest_honest(self):
        by = {r["id"]: r for r in self._get("/api/tasks").json()["battles"]}
        # 计数如实(ledger_reader soldiers_now/findings_list 长度,不筛态)
        self.assertEqual(by["battle-1"]["goal"], "G-r18")
        self.assertEqual(by["battle-1"]["soldiers_n"], 6)
        self.assertEqual(by["battle-1"]["findings_n"], 76)
        self.assertEqual(by["battle-1"]["latest_ts"], "2026-10-14T13:31:00Z")
        self.assertEqual(by["battle-1"]["name"], "authorized-range.local")
        self.assertEqual(by["battle-2"]["soldiers_n"], 2)
        self.assertEqual(by["battle-2"]["findings_n"], 3)
        self.assertEqual(by["battle-2"]["latest_ts"], "2026-10-14T14:30:00Z")
        self.assertEqual(by["battle-2"]["name"], "demo-target")
        self.assertEqual(by["battle-3"]["soldiers_n"], 0)
        self.assertEqual(by["battle-3"]["findings_n"], 0)
        self.assertEqual(by["battle-3"]["latest_ts"], "2026-10-14T09:45:00Z")
        self.assertEqual(by["battle-4"]["soldiers_n"], 1)
        # 无代 goal 的草稿仗: 零计数+latest None,不造假
        self.assertEqual(by["battle-5"]["goal"], "")
        self.assertEqual(by["battle-5"]["soldiers_n"], 0)
        self.assertEqual(by["battle-5"]["findings_n"], 0)
        self.assertIsNone(by["battle-5"]["latest_ts"])
        self.assertEqual(by["battle-5"]["name"], "")

    def test_badge_derived_same_source(self):
        for r in self._get("/api/tasks").json()["battles"]:
            self.assertEqual(r["badge"], _badge_of(r["id"]))

    def test_empty_root_zero_battles(self):
        empty = tempfile.mkdtemp(prefix="readface-t11-empty-")
        self.addCleanup(shutil.rmtree, empty, True)
        with mock.patch.dict(os.environ, {"TANYIN_HOME": empty}):
            resp = self.client.get("/api/tasks")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"battles": []})


class TaskDetailTests(_Base):
    """/api/tasks/{id}: 列表字段+goals 简述+会话分组(战士/意图线索)。"""

    def test_detail_warrior_sessions_grouping(self):
        resp = self._get("/api/tasks/battle-4")
        self.assertEqual(resp.status_code, 200)
        doc = resp.json()
        self.assertEqual(set(doc) - {"sessions", "objective"},
                         {"id", "name", "status", "status_detail", "running",
                          "badge", "goal", "soldiers_n", "findings_n",
                          "latest_ts"})
        self.assertEqual(doc["id"], "battle-4")
        self.assertEqual(doc["name"], "warrior-target")
        self.assertEqual(doc["objective"], "会话签分组演示仗")
        self.assertEqual(doc["latest_ts"], "2026-10-14T09:00:45Z")
        # 两组: deck(2 行: add-goal/deck-halt;deck-halt 09:00:45 最新
        # 居首)+战士 w1(5 行: start/heartbeat/http-get/steer/stop)——
        # 组序=last_ts 新→旧
        sessions = doc["sessions"]
        self.assertEqual([s["session_key"] for s in sessions],
                         ["deck", "w:w1"])
        for s in sessions:
            self.assertEqual(set(s),
                             {"session_key", "label", "rows_n",
                              "first_ts", "last_ts"})
        by_key = {s["session_key"]: s for s in sessions}
        w1 = by_key["w:w1"]
        self.assertEqual(w1["label"], "战士 w1")
        self.assertEqual(w1["rows_n"], 5)
        self.assertEqual(w1["first_ts"], "2026-10-14T09:00:05Z")
        self.assertEqual(w1["last_ts"], "2026-10-14T09:00:40Z")
        deck = by_key["deck"]
        self.assertEqual(deck["label"], "战役本级")
        self.assertEqual(deck["rows_n"], 2)
        self.assertEqual(deck["first_ts"], "2026-10-14T09:00:00Z")
        self.assertEqual(deck["last_ts"], "2026-10-14T09:00:45Z")
        # 分组并集=该仗全部行(无重无漏)
        self.assertEqual(w1["rows_n"] + deck["rows_n"], 7)

    def test_detail_intent_sessions_and_order(self):
        doc = self._get("/api/tasks/battle-1").json()
        sessions = doc["sessions"]
        # G-r18 无 warrior 行: 6 个 add-intent 意图组+deck(709-6=703 行)
        self.assertEqual(len(sessions), 7)
        by = {s["session_key"]: s for s in sessions}
        self.assertEqual(by["deck"]["rows_n"], 703)
        i1 = by["i:INT-r18-0001"]
        self.assertEqual(i1["rows_n"], 1)
        self.assertEqual(i1["label"], "意图 INT-r18-0001 · port-scan-8000-8010")
        # 组序: last_ts 新→旧(deck 13:31 最新居首,意图组按 add-intent 时刻)
        self.assertEqual(sessions[0]["session_key"], "deck")
        self.assertEqual(sessions[-1]["session_key"], "i:INT-r18-0001")

    def test_detail_deck_only_battle(self):
        doc = self._get("/api/tasks/battle-2").json()
        sessions = doc["sessions"]
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["session_key"], "deck")
        self.assertEqual(sessions[0]["rows_n"], 4)
        self.assertEqual(sessions[0]["first_ts"], "2026-10-14T07:30:00Z")
        self.assertEqual(sessions[0]["last_ts"], "2026-10-14T14:30:00Z")

    def test_detail_draft_battle_empty_sessions(self):
        doc = self._get("/api/tasks/battle-5").json()
        self.assertEqual(doc["status"], "草稿")
        self.assertEqual(doc["sessions"], [])

    def test_detail_unknown_battle_404(self):
        resp = self._get("/api/tasks/no-such-battle")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("error", resp.json())


class SessionStreamTests(_Base):
    """/api/tasks/{id}/sessions/{key}: 组内时刻流(T5 行形状+badge+翻页)。"""

    def _walk(self, battle, key, limit=2):
        seen, cursor = [], None
        for _ in range(50):
            params = {"limit": limit}
            if cursor:
                params["before_key"] = cursor
            resp = self._get("/api/tasks/%s/sessions/%s" % (battle, key),
                             **params)
            self.assertEqual(resp.status_code, 200)
            doc = resp.json()
            seen.extend(doc["rows"])
            cursor = doc["next_cursor"]
            if cursor is None:
                break
        return seen, resp.json()

    def test_row_shape_and_order(self):
        resp = self._get("/api/tasks/battle-4/sessions/w:w1", limit=50)
        self.assertEqual(resp.status_code, 200)
        doc = resp.json()
        self.assertEqual(set(doc), {"rows", "next_cursor"})
        rows = doc["rows"]
        self.assertEqual(len(rows), 5)
        for it in rows:
            self.assertEqual(set(it),
                             {"key", "ts", "kind", "detail",
                              "battle", "badge"})
            self.assertEqual(it["battle"], "battle-4")
            self.assertEqual(it["badge"], _badge_of("battle-4"))
        # 组内新→旧;steer/stop 留痕在战士组内
        self.assertEqual([r["kind"] for r in rows],
                         ["warrior-stop", "warrior-steer",
                          "http-get", "warrior-heartbeat", "warrior-start"])
        self.assertTrue(rows[1]["detail"].startswith("warrior-steer target=w1"))

    def test_pagination_full_chain_no_dup_no_gap(self):
        seen, last = self._walk("battle-4", "w:w1", limit=2)
        self.assertEqual(len(seen), 5)
        keys = [r["key"] for r in seen]
        self.assertEqual(len(keys), len(set(keys)))          # 无重
        # 无漏: 并集=组内全量(整组直取对照,ledger_reader 单源)
        whole = self._get("/api/tasks/battle-4/sessions/w:w1",
                          limit=50).json()["rows"]
        self.assertEqual(set(keys), {r["key"] for r in whole})
        self.assertEqual(last["rows"], [seen[-1]])           # 末页恰 1 行
        # 跨页 ts 单调不增
        for a, b in zip(seen, seen[1:]):
            self.assertGreaterEqual(a["ts"], b["ts"])

    def test_deck_group_stream(self):
        resp = self._get("/api/tasks/battle-4/sessions/deck", limit=1)
        doc = resp.json()
        self.assertEqual(len(doc["rows"]), 1)
        self.assertEqual(doc["rows"][0]["kind"], "deck-halt")   # 新→旧首行
        self.assertIsNotNone(doc["next_cursor"])

    def test_unknown_battle_and_session_404(self):
        resp = self._get("/api/tasks/no-such-battle/sessions/deck")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("error", resp.json())
        resp = self._get("/api/tasks/battle-4/sessions/w:w2")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("error", resp.json())

    def test_bad_or_cross_group_cursor_400(self):
        # 坏游标: 不在链上的乱串
        resp = self._get("/api/tasks/battle-4/sessions/w:w1",
                         before_key="f" * 64)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json())
        # 跨组游标: deck 组最旧行的 key 拿去 w:w1 组翻页 → 400(不在该组)
        deck_rows = self._get("/api/tasks/battle-4/sessions/deck",
                              limit=50).json()["rows"]
        deck_oldest = deck_rows[-1]["key"]
        resp = self._get("/api/tasks/battle-4/sessions/w:w1",
                         before_key=deck_oldest)
        self.assertEqual(resp.status_code, 400)

    def test_limit_validation(self):
        for bad in ("0", "-3", "abc"):
            resp = self._get("/api/tasks/battle-4/sessions/w:w1", limit=bad)
            self.assertEqual(resp.status_code, 422, "limit=%s 须 422" % bad)


class ZeroSideEffectTests(unittest.TestCase):
    """纯读铁律: 列表+详情+组流翻页+坏游标打一遍,树纹丝不动。"""

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

    def test_tasks_endpoints_leave_battles_tree_untouched(self):
        syn = _SyntheticHome()
        self.addCleanup(syn.cleanup)
        before = self._snapshot(syn.home)
        client = TestClient(app)
        with mock.patch.dict(os.environ, {"TANYIN_HOME": syn.home}):
            client.get("/api/tasks")
            client.get("/api/tasks/battle-1")
            client.get("/api/tasks/battle-4")
            client.get("/api/tasks/battle-5")
            client.get("/api/tasks/battle-nope")
            doc = client.get("/api/tasks/battle-4/sessions/w:w1",
                             params={"limit": 2}).json()
            cursor = doc["next_cursor"]
            if cursor:
                client.get("/api/tasks/battle-4/sessions/w:w1",
                           params={"limit": 2, "before_key": cursor})
            client.get("/api/tasks/battle-4/sessions/w:w1",
                       params={"before_key": "f" * 64})
        self.assertEqual(self._snapshot(syn.home), before)


if __name__ == "__main__":
    unittest.main()
