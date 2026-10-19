# -*- coding: utf-8 -*-
"""T2 账本读投影测试(测试先行:先跑红,再实现跑绿)。

覆盖四投影 × 形状/排序/游标分页/灰卡分离:
- timeline_tail: 默认尾 50 条新→旧;limit 生效;before_key 游标反向分页
  走全链无重无漏;未知 key fail-loud;最老 key → 空页。
- findings_list: 键形/按 id 排序;verified=机器复放验真(VERIFIED/REPAIRED);
  replay_state 三态 已验/待验(灰卡)/复验中 分得开;status 过滤走最新行。
- soldiers_now: corps 经兵种位/kind 路由;heartbeat_ts 夹具缺=不造假(None);
  tokens=budget_share 首段。
- approvals_pending: 待审=引擎 cleanup-checklist 同源 pending;reverted/exempted
  出队;id=sha256(revert_cmd);timeout_policy 读 approval.json;risk_line 词表单源。
- 纯读零 side effect: 四函数跑一遍,夹具树字节+mtime 全不变。

数据源: tests/fixtures/G-r18 夹具账本(实数断言)+ tempfile 合成微型 goal
(用引擎 chained_row 真实接链,只写临时目录,不碰夹具/引擎一行)。

运行(仓库根): PYTHONPATH=cli python3 -m unittest tests.readface.test_reader -v
"""
import hashlib
import os
import re
import shutil
import tempfile
import unittest

# ledger_reader 导入即把仓根 cli/ 前上 sys.path(PYTHONPATH=cli 同效),
# 故后续 `from ledger import ...` 在两种跑法下都成立。
from server.readface import ledger_reader

from ledger import core as ledger_core
from ledger import timeline as ledger_timeline
from ledger.schemas import TABLES


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
FIXTURE = os.path.join(REPO_ROOT, "tests", "fixtures", "G-r18")
TL_COLS = TABLES["timeline.tsv"]


def _chain(spec):
    """[(ts,actor,phase,event,revert_cmd)...] → 引擎真实接链的 8 列行。"""
    rows = []
    for ts, actor, phase, event, revert in spec:
        row, _ = ledger_timeline.chained_row(rows, ts, actor, phase, event, revert)
        rows.append(row)
    return rows


class _SyntheticGoalMixin(object):
    """tempfile 合成微型 goal(引擎 write_tsv 落盘,addCleanup 收尾)。"""

    def mk_goal(self, tl_spec, extra=None):
        gd = tempfile.mkdtemp(prefix="readface-t2-")
        self.addCleanup(shutil.rmtree, gd, True)
        ledger_core.write_tsv(os.path.join(gd, "timeline.tsv"), _chain(tl_spec))
        for tname, dict_rows in (extra or {}).items():
            cols = TABLES[tname]
            ledger_core.write_tsv(
                os.path.join(gd, tname),
                [[d.get(c, "") for c in cols] for d in dict_rows])
        return gd


class TimelineTailTests(unittest.TestCase):
    """①timeline_tail: key 游标反向分页。"""

    def test_default_shape_and_newest_first_order(self):
        items = ledger_reader.timeline_tail(FIXTURE)
        self.assertEqual(len(items), 50)          # 缺省 limit=50
        for it in items:
            self.assertEqual(set(it), {"key", "ts", "kind", "detail"})
            self.assertTrue(it["key"])
            self.assertTrue(it["kind"])
        # 新→旧: 相邻 ts 不增(文件序倒读)
        for a, b in zip(items, items[1:]):
            self.assertGreaterEqual(a["ts"], b["ts"])
        # 首条=文件最末行(尾读语义),key=该行链哈希
        raw = ledger_core.read_tsv(os.path.join(FIXTURE, "timeline.tsv"), 8)
        last = raw[-1]
        self.assertEqual(items[0]["key"], last[TL_COLS.index("hash")])
        self.assertEqual(items[0]["ts"], last[TL_COLS.index("timestamp")])
        self.assertEqual(items[0]["detail"], last[TL_COLS.index("event")])

    def test_limit_respected_and_matches_tail(self):
        items = ledger_reader.timeline_tail(FIXTURE, limit=5)
        self.assertEqual(len(items), 5)
        raw = ledger_core.read_tsv(os.path.join(FIXTURE, "timeline.tsv"), 8)
        expected = list(reversed(raw[-5:]))
        self.assertEqual([it["key"] for it in items],
                         [r[TL_COLS.index("hash")] for r in expected])

    def test_cursor_pagination_walks_whole_chain_no_dup_no_gap(self):
        seen, cursor, pages = [], None, 0
        while True:
            page = ledger_reader.timeline_tail(FIXTURE, before_key=cursor, limit=7)
            if not page:
                break
            pages += 1
            seen.extend(page)
            cursor = page[-1]["key"]           # 页内最旧 key 作下页游标
            self.assertLessEqual(pages, 200)
        raw = ledger_core.read_tsv(os.path.join(FIXTURE, "timeline.tsv"), 8)
        self.assertEqual(len(seen), len(raw))               # 709 全覆盖
        self.assertEqual(len({it["key"] for it in seen}), len(raw))  # 零重复
        whole = ledger_reader.timeline_tail(FIXTURE, before_key=cursor, limit=7)
        self.assertEqual(whole, [])                          # 游标到底=空页
        # 与全量倒序一致
        all_items = ledger_reader.timeline_tail(FIXTURE, limit=len(raw))
        self.assertEqual([it["key"] for it in seen],
                         [it["key"] for it in all_items])

    def test_unknown_before_key_fails_loud(self):
        with self.assertRaises(ValueError):
            ledger_reader.timeline_tail(FIXTURE, before_key="deadbeef", limit=5)


class FindingsListTests(_SyntheticGoalMixin, unittest.TestCase):
    """②findings_list: 验真态+灰卡三态。"""

    def test_fixture_shape_sorted_and_tri_state_counts(self):
        items = ledger_reader.findings_list(FIXTURE)
        self.assertEqual(len(items), 76)        # 111 行去重(事件溯源取最新)
        ids = [it["id"] for it in items]
        self.assertEqual(ids, sorted(ids))      # 按 id 稳定排序
        for it in items:
            self.assertEqual(
                set(it),
                {"id", "sev", "where", "title", "verified", "replay_state", "ts"})
            self.assertIsInstance(it["verified"], bool)
            self.assertIn(it["replay_state"], ("已验", "待验", "复验中"))
            self.assertIn(it["sev"], ("C1", "C2", "C3"))
            self.assertRegex(it["ts"], r"^2026-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        # G-r18 实况: 63 个 EV 终态 VERIFIED + 1 个 probe 在途(EV-r18-0102)
        states = [it["replay_state"] for it in items]
        self.assertEqual(states.count("已验"), 75)
        self.assertEqual(states.count("复验中"), 1)
        self.assertEqual(states.count("待验"), 0)
        # 在途那条=FD-r18-0076(EV-r18-0102 probe 未落终态),机器验真未过
        f76 = next(it for it in items if it["id"] == "FD-r18-0076")
        self.assertEqual(f76["replay_state"], "复验中")
        self.assertFalse(f76["verified"])

    def test_fixture_verified_matches_replay_state(self):
        items = ledger_reader.findings_list(FIXTURE)
        for it in items:
            if it["replay_state"] == "已验":
                self.assertTrue(it["verified"])
            else:
                self.assertFalse(it["verified"])
        self.assertEqual(sum(1 for it in items if it["verified"]), 75)

    def test_synthetic_grey_card_tri_state_separation(self):
        gd = self.mk_goal(
            [("2026-10-14T10:00:0%dZ" % i, "replay", "P4", ev, "")
             for i, ev in enumerate([
                 "replay-probe EV-s-A verdict=reproduced",   # 只探未判=复验中
                 "replay:EV-s-B:VERIFIED",                    # 已验
                 "replay:EV-s-D:REJECTED",                    # 复放未过=灰卡待验
                 "replay:EV-s-E:VERIFIED",                    # 已验后再探=复验中
                 "replay-probe EV-s-E verdict=reproduced",
             ])],
            {"findings.tsv": [
                {"id": "FD-s-A", "title": "probe-only", "confidence": "C2",
                 "impact": "低", "status": "active", "evidence_ids": "EV-s-A",
                 "affected_asset_id": "AST-s-1", "created": "2026-10-14T10:01:00Z"},
                {"id": "FD-s-B", "title": "verified", "confidence": "C1",
                 "impact": "高", "status": "active", "evidence_ids": "EV-s-B",
                 "affected_asset_id": "AST-s-2", "created": "2026-10-14T10:02:00Z"},
                {"id": "FD-s-C", "title": "no-replay", "confidence": "C3",
                 "impact": "低", "status": "active", "evidence_ids": "EV-s-C",
                 "affected_asset_id": "", "created": "2026-10-14T10:03:00Z"},
                {"id": "FD-s-D", "title": "rejected", "confidence": "C2",
                 "impact": "中", "status": "active", "evidence_ids": "EV-s-D",
                 "affected_asset_id": "AST-s-4", "created": "2026-10-14T10:04:00Z"},
                {"id": "FD-s-E", "title": "re-verify", "confidence": "C1",
                 "impact": "高", "status": "active", "evidence_ids": "EV-s-E",
                 "affected_asset_id": "AST-s-5", "created": "2026-10-14T10:05:00Z"},
            ]})
        by_id = {it["id"]: it for it in ledger_reader.findings_list(gd)}
        self.assertEqual(by_id["FD-s-A"]["replay_state"], "复验中")
        self.assertFalse(by_id["FD-s-A"]["verified"])
        self.assertEqual(by_id["FD-s-B"]["replay_state"], "已验")
        self.assertTrue(by_id["FD-s-B"]["verified"])
        self.assertEqual(by_id["FD-s-C"]["replay_state"], "待验")
        self.assertFalse(by_id["FD-s-C"]["verified"])
        self.assertIsNone(by_id["FD-s-C"]["where"])   # 缺列宁缺毋假=null
        self.assertEqual(by_id["FD-s-D"]["replay_state"], "待验")
        self.assertFalse(by_id["FD-s-D"]["verified"])
        # 已验后又在复验: 历史终态已过=verified,过程态=复验中
        self.assertEqual(by_id["FD-s-E"]["replay_state"], "复验中")
        self.assertTrue(by_id["FD-s-E"]["verified"])

    def test_status_filter_uses_latest_row(self):
        gd = self.mk_goal(
            [("2026-10-14T10:00:00Z", "CLI", "P0", "add-finding FD-s-1", ""),
             ("2026-10-14T10:00:01Z", "CLI", "P0", "add-finding FD-s-2", ""),
             ("2026-10-14T10:00:02Z", "CLI", "P0", "supersede-finding FD-s-1", "")],
            {"findings.tsv": [
                {"id": "FD-s-1", "title": "v1", "status": "active",
                 "created": "2026-10-14T10:00:00Z"},
                {"id": "FD-s-2", "title": "v2", "status": "active",
                 "created": "2026-10-14T10:00:01Z"},
                {"id": "FD-s-1", "title": "v2-of-1", "status": "superseded",
                 "created": "2026-10-14T10:00:02Z"},
            ]})
        self.assertEqual(len(ledger_reader.findings_list(gd)), 2)  # 缺省=全量
        active = ledger_reader.findings_list(gd, status="active")
        self.assertEqual([it["id"] for it in active], ["FD-s-2"])
        sup = ledger_reader.findings_list(gd, status="superseded")
        self.assertEqual([it["id"] for it in sup], ["FD-s-1"])
        self.assertEqual(sup[0]["title"], "v2-of-1")   # 事件溯源取最新行


class SoldiersNowTests(_SyntheticGoalMixin, unittest.TestCase):
    """③soldiers_now: 兵种路由/心跳/预算 token。"""

    def test_fixture_shape_routes_and_tokens(self):
        items = ledger_reader.soldiers_now(FIXTURE)
        self.assertEqual(len(items), 6)
        by_intent = {it["intent"]: it for it in items}
        self.assertEqual(
            list(by_intent),
            ["port-scan-8000-8010", "drill-three-forms-mechanics",
             "dict-wave-anonymous", "credential-issuance-wave",
             "post-auth-rescan-checklist", "newclass-hunt"])
        for it in items:
            self.assertEqual(
                set(it), {"corps", "intent", "status", "heartbeat_ts", "tokens"})
            self.assertIn(it["corps"], ("pentest-recon", "pentest-enum",
                                         "pentest-exploit"))
            self.assertEqual(it["status"], "pending")
        # kind 路由(warrior.corps 缺省表单源): recon→侦察/surface→枚举/matrix-test→渗透
        self.assertEqual(by_intent["port-scan-8000-8010"]["corps"], "pentest-recon")
        self.assertEqual(
            by_intent["drill-three-forms-mechanics"]["corps"], "pentest-enum")
        self.assertEqual(
            by_intent["dict-wave-anonymous"]["corps"], "pentest-exploit")
        # tokens=budget_share 首段(tokens;requests;hours)
        self.assertEqual(by_intent["port-scan-8000-8010"]["tokens"], 100000)
        self.assertEqual(by_intent["drill-three-forms-mechanics"]["tokens"], 10000)
        self.assertEqual(by_intent["dict-wave-anonymous"]["tokens"], 200000)

    def test_fixture_heartbeat_absent_is_null_not_fabricated(self):
        # G-r18 无 warrior-heartbeat 行: heartbeat_ts 全 None(宁缺毋假)
        for it in ledger_reader.soldiers_now(FIXTURE):
            self.assertIsNone(it["heartbeat_ts"])

    def test_synthetic_heartbeat_marker_and_missing_route(self):
        gd = self.mk_goal(
            [("2026-10-14T10:00:00Z", "warrior:w1", "P-lifecycle",
              "warrior-heartbeat warrior=w1 intent=INT-s-1", ""),
             ("2026-10-14T10:05:00Z", "warrior:w1", "P-lifecycle",
              "warrior-heartbeat warrior=w1 intent=INT-s-1 tokens=42", ""),
             ("2026-10-14T10:06:00Z", "warrior:w2", "P-lifecycle",
              "warrior-heartbeat warrior=w2 intent=INT-s-2 extra=x", "")],
            {"intents.tsv": [
                {"id": "INT-s-1", "title": "scan-east", "status": "active",
                 "kind": "recon", "budget_share": "2M;100;1"},
                {"id": "INT-s-2", "title": "verify-card", "status": "pending",
                 "kind": "recon", "detail": "[corps:pentest-verify]",
                 "budget_share": ""},
                {"id": "INT-s-3", "title": "biz-logic-diff", "status": "blocked",
                 "kind": "authz-diff", "budget_share": "500;10;1"},
            ]})
        items = ledger_reader.soldiers_now(gd)
        by_id = {it["intent"]: it for it in items}
        # 最新心跳胜出(10:05>10:00),extra 段不干扰 intent= 抽取
        self.assertEqual(by_id["scan-east"]["heartbeat_ts"],
                         "2026-10-14T10:05:00Z")
        self.assertEqual(by_id["verify-card"]["heartbeat_ts"],
                         "2026-10-14T10:06:00Z")
        # 兵种位 [corps:X] 直读优先于 kind 缺省路由
        self.assertEqual(by_id["scan-east"]["corps"], "pentest-recon")
        self.assertEqual(by_id["verify-card"]["corps"], "pentest-verify")
        # authz-diff 无缺省兵种(R-CORPS-1)=null 不造假;budget 缺=null
        self.assertIsNone(by_id["biz-logic-diff"]["corps"])
        self.assertIsNone(by_id["verify-card"]["tokens"])
        # 2M 解析=2000000;状态原样透传
        self.assertEqual(by_id["scan-east"]["tokens"], 2000000)
        self.assertEqual(by_id["biz-logic-diff"]["status"], "blocked")


class ApprovalsPendingTests(_SyntheticGoalMixin, unittest.TestCase):
    """④approvals_pending: 引擎 cleanup-checklist 同源待审。"""

    def test_fixture_empty_because_no_revert_cmd_rows(self):
        # G-r18 timeline revert_cmd 列全空: 待审清单诚实为空(零假数)
        self.assertEqual(ledger_reader.approvals_pending(FIXTURE), [])

    def test_synthetic_pending_shape_order_and_settlement(self):
        gd = self.mk_goal(
            [("2026-10-14T10:00:00Z", "op", "P3",
              "http-get http://x/a", "rollback-get-a"),
             ("2026-10-14T10:01:00Z", "op", "P3",
              "deploy payload", "rollback-deploy"),
             ("2026-10-14T10:02:00Z", "op", "P3",
              "revert:http-get http://x/a", ""),                # 核销第1条
             ("2026-10-14T10:03:00Z", "op", "P3",
              "wget http://y", "rollback-wget"),
             ("2026-10-14T10:04:00Z", "op", "P3",
              "mystery-op foo", "rollback-mystery")],
            {"approvals.tsv": [
                # 豁免第 wget 条(decision=exempted 且 note 含原事件文本)
                {"id": "AP-s-1", "decision": "exempted", "approver": "u",
                 "timestamp": "2026-10-14T10:03:30Z",
                 "note": "预授权零打扰放行 原事件:wget http://y"},
            ]})
        items = ledger_reader.approvals_pending(gd)
        self.assertEqual(len(items), 2)               # deploy+mystery 在队
        for it in items:
            self.assertEqual(set(it),
                             {"id", "event", "risk_line", "timeout_policy", "ts"})
        # 文件序(挂起先后)且 ts 对位
        self.assertEqual([it["event"] for it in items],
                         ["deploy payload", "mystery-op foo"])
        self.assertEqual([it["ts"] for it in items],
                         ["2026-10-14T10:01:00Z", "2026-10-14T10:04:00Z"])
        # id=sha256(revert_cmd)——approve 通道 --command-hash 同键
        self.assertEqual(
            [it["id"] for it in items],
            [hashlib.sha256(b"rollback-deploy").hexdigest(),
             hashlib.sha256(b"rollback-mystery").hexdigest()])
        # 夹具无 approval.json → 缺省 30 分钟超时保守
        for it in items:
            self.assertIn("30", it["timeout_policy"])

    def test_synthetic_risk_line_wordlist_and_timeout_config(self):
        gd = self.mk_goal(
            [("2026-10-14T10:00:00Z", "op", "P3",
              "curl http://a", "rb-curl"),
             ("2026-10-14T10:00:01Z", "op", "P3",
              "rm -rf /tmp/x", "rb-rm"),
             ("2026-10-14T10:00:02Z", "op", "P3",
              "weird-thing", "rb-weird")])
        with open(os.path.join(gd, "approval.json"), "w", encoding="utf-8") as f:
            f.write('{"timeout_min": 5}')
        items = ledger_reader.approvals_pending(gd)
        by_event = {it["event"]: it for it in items}
        # 词表单源(preauth._READ_VERBS/_DANGER_MARKS)三类判读
        self.assertIn("只读", by_event["curl http://a"]["risk_line"])
        self.assertIn("高危", by_event["rm -rf /tmp/x"]["risk_line"])
        self.assertIsNone(by_event["weird-thing"]["risk_line"])  # 判不了=null
        self.assertIn("5", items[0]["timeout_policy"])           # 配置生效


class ZeroSideEffectTests(unittest.TestCase):
    """纯读铁律: 四投影跑一遍,夹具树字节+mtime 纹丝不动。"""

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

    def test_all_four_reads_leave_fixture_untouched(self):
        before = self._snapshot(FIXTURE)
        ledger_reader.timeline_tail(FIXTURE, limit=3)
        ledger_reader.findings_list(FIXTURE)
        ledger_reader.soldiers_now(FIXTURE)
        ledger_reader.approvals_pending(FIXTURE)
        self.assertEqual(self._snapshot(FIXTURE), before)


if __name__ == "__main__":
    unittest.main()
