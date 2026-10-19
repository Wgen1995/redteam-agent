# -*- coding: utf-8 -*-
"""T8 内联审批读面测试(测试先行:先跑红,再实现跑绿)。

覆盖(件A routers/approvals.py + engine_bridge approve 扩段 +
ledger_reader.approvals_pending 决定回链出队):
- 批准流: POST /api/chat/approve{battle,command_hash,decision:approve}
  → 桥子进程 tanyin-ledger approve --command-hash 同键 → 200;
  读回 approvals_pending 消项(该 command_hash 出队,余项保留);
  approvals.tsv 新增 decision=approved 行(command_hash 逐字对照);
  timeline 新增 "approve AP-*(approved)" 事件且链完整(verify_chain)。
- 拒绝流: decision:reject → decision=rejected 同律消项+记录拒。
- 决定回链(引擎 webui W6 同律): approvals 行 note 含原事件文本 →
  待审项出队(核销口径 _replay_status 不变——revert/exempted 照旧)。
- 未知识别: 未知 command_hash→404;未知 battle→404;decision 词表外→422;
  已决重审→404(一次一决定,不覆写)。
- 桥失败 502 不造假: 桥子进程 rc!=0→502 {error} 待审不动;
  桥回执 ok 但读回未消项(读写不一致)→502 如实报。
- 桥真子进程(TANYIN_HOME 合成根): approve 落链回执 ok+approval_id;
  note 含原事件文本(回链锚)+approver/timestamp 真值;未知哈希/缺参/
  decision 词表外→rc=2;TANYIN_APPROVAL_KEY 在场→自动 --sig 签发落链。

运行(仓库根): PYTHONPATH=cli python3 -m unittest tests.readface.test_approvals -v
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from server.readface.main import app
from server.readface.routers import approvals as approvals_router
from server.readface import ledger_reader

from ledger import core as ledger_core
from ledger import timeline as ledger_timeline
from ledger.schemas import TABLES

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
BRIDGE = os.path.join(REPO_ROOT, "server", "readface", "engine_bridge.py")

EV1 = "http-get http://10.2.0.7:8080/admin"      # 待审项1(批)
RB1 = "rollback-http-get-admin"
EV2 = "deploy payload staging"                   # 待审项2(留队对照)
RB2 = "rollback-deploy-staging"
H1 = hashlib.sha256(RB1.encode("utf-8")).hexdigest()
H2 = hashlib.sha256(RB2.encode("utf-8")).hexdigest()

TL_SPEC = [
    ("2026-10-14T10:00:00Z", "op", "P0", "add-goal G-1", ""),
    ("2026-10-14T11:00:00Z", "warrior:w1", "P3", EV1, RB1),
    ("2026-10-14T11:30:00Z", "warrior:w1", "P3", EV2, RB2),
]


def _chain(spec):
    """[(ts,actor,phase,event,revert_cmd)...] → 引擎真实接链 8 列行。"""
    rows = []
    for ts, actor, phase, event, revert in spec:
        row, _ = ledger_timeline.chained_row(rows, ts, actor, phase, event, revert)
        rows.append(row)
    return rows


def mk_battle_home():
    """合成 TANYIN_HOME: battles/battle-2/G-1 微型 goal(tier0 goals 行+
    两条 revert_cmd 待审)+runner 已点火;返回 (home, goal_dir)。"""
    home = tempfile.mkdtemp(prefix="readface-t8-home-")
    goal_dir = os.path.join(home, "battles", "battle-2", "G-1")
    os.makedirs(goal_dir)
    ledger_core.write_tsv(os.path.join(goal_dir, "timeline.tsv"), _chain(TL_SPEC))
    goal = {"id": "G-t8", "target": "demo-target",
            "created": "2026-10-14T10:00:00Z"}
    ledger_core.write_tsv(
        os.path.join(goal_dir, "goals.tsv"),
        [[goal.get(c, "") for c in TABLES["goals.tsv"]]])
    battle_dir = os.path.dirname(goal_dir)
    with open(os.path.join(battle_dir, "opencode-run.log.runner.tsv"),
              "w", encoding="utf-8") as f:
        f.write("2026-10-14T10:00:01Z\tBOOT\tup\n"
                "2026-10-14T10:00:05Z\tLAUNCH\topencode\n")
    return home, goal_dir


def _ap_rows(goal_dir):
    s = ledger_core.Session(goal_dir)
    return s.rows("approvals.tsv"), s


class PendingDecidedLinkTests(unittest.TestCase):
    """决定回链出队(引擎 webui _approval_projection 同律,读回消项的地基)。"""

    def setUp(self):
        self.home, self.goal_dir = mk_battle_home()
        self.addCleanup(shutil.rmtree, self.home, True)

    def test_pending_two_items_before_any_decision(self):
        items = ledger_reader.approvals_pending(self.goal_dir)
        self.assertEqual([it["id"] for it in items], [H1, H2])   # 文件序
        self.assertEqual([it["event"] for it in items], [EV1, EV2])

    def test_approved_row_with_event_in_note_leaves_queue(self):
        cols = TABLES["approvals.tsv"]
        ledger_core.write_tsv(
            os.path.join(self.goal_dir, "approvals.tsv"),
            [[{"id": "AP-1-0001", "command_hash": H1, "decision": "approved",
               "approver": "操作员(指挥台)", "timestamp": "2026-10-14T12:00:00Z",
               "note": EV1 + "（指挥台审批）"}.get(c, "") for c in cols]])
        items = ledger_reader.approvals_pending(self.goal_dir)
        self.assertEqual([it["id"] for it in items], [H2])       # H1 出队

    def test_rejected_row_with_event_in_note_leaves_queue(self):
        cols = TABLES["approvals.tsv"]
        ledger_core.write_tsv(
            os.path.join(self.goal_dir, "approvals.tsv"),
            [[{"id": "AP-1-0001", "command_hash": H2, "decision": "rejected",
               "approver": "操作员(指挥台)", "timestamp": "2026-10-14T12:00:00Z",
               "note": EV2 + "（指挥台审批）"}.get(c, "") for c in cols]])
        items = ledger_reader.approvals_pending(self.goal_dir)
        self.assertEqual([it["id"] for it in items], [H1])

    def test_note_without_event_text_keeps_pending(self):
        cols = TABLES["approvals.tsv"]
        ledger_core.write_tsv(
            os.path.join(self.goal_dir, "approvals.tsv"),
            [[{"id": "AP-1-0001", "command_hash": H1, "decision": "approved",
               "approver": "操作员(指挥台)", "timestamp": "2026-10-14T12:00:00Z",
               "note": "批了别的命令（无回链锚）"}.get(c, "") for c in cols]])
        self.assertEqual([it["id"] for it in items_of(self.goal_dir)], [H1, H2])


def items_of(goal_dir):
    return ledger_reader.approvals_pending(goal_dir)


class ApproveEndpointBase(unittest.TestCase):
    def setUp(self):
        self.home, self.goal_dir = mk_battle_home()
        self.addCleanup(shutil.rmtree, self.home, True)
        self.client = TestClient(app)

    def _post(self, **body):
        with mock.patch.dict(os.environ, {"TANYIN_HOME": self.home}):
            return self.client.post("/api/chat/approve", json=body)


class TestApproveFlow(ApproveEndpointBase):
    """批→消项+链上审批记录;拒→消项+记录拒。"""

    def test_approve_removes_pending_and_records_on_chain(self):
        r = self._post(battle="battle-2", command_hash=H1, decision="approve")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["decision"], "approve")
        self.assertTrue(body["approval_id"].startswith("AP-"))
        self.assertEqual(body["pending_left"], 1)
        # 消项(读回): H1 出队,H2 留守
        self.assertEqual([it["id"] for it in items_of(self.goal_dir)], [H2])
        # 链上新增审批记录: approvals.tsv 行逐字对照 + timeline 事件 + 链完整
        rows, s = _ap_rows(self.goal_dir)
        self.assertEqual(len(rows), 1)
        i_hash = TABLES["approvals.tsv"].index("command_hash")
        i_dec = TABLES["approvals.tsv"].index("decision")
        i_note = TABLES["approvals.tsv"].index("note")
        self.assertEqual(rows[0][i_hash], H1)
        self.assertEqual(rows[0][i_dec], "approved")
        self.assertIn(EV1, rows[0][i_note])            # 决定回链锚
        i_ev = TABLES["timeline.tsv"].index("event")
        self.assertTrue(any(r0[i_ev].startswith("approve AP-") and
                            "approved" in r0[i_ev]
                            for r0 in s.rows("timeline.tsv")))
        ok, bad = s.verify_chain()
        self.assertTrue(ok, "审批后链断裂于第 %d 行" % bad)

    def test_reject_removes_pending_and_records_rejected(self):
        r = self._post(battle="battle-2", command_hash=H2, decision="reject")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["decision"], "reject")
        self.assertEqual(body["pending_left"], 1)
        self.assertEqual([it["id"] for it in items_of(self.goal_dir)], [H1])
        rows, _s = _ap_rows(self.goal_dir)
        i_dec = TABLES["approvals.tsv"].index("decision")
        self.assertEqual(rows[0][i_dec], "rejected")

    def test_optional_note_lands_in_ledger(self):
        r = self._post(battle="battle-2", command_hash=H1, decision="approve",
                       note="靶场演练回滚无忧")
        self.assertEqual(r.status_code, 200, r.text)
        rows, _s = _ap_rows(self.goal_dir)
        i_note = TABLES["approvals.tsv"].index("note")
        self.assertIn("靶场演练回滚无忧", rows[0][i_note])
        self.assertIn(EV1, rows[0][i_note])            # 锚与补充说明共存


class TestApproveUnknowns(ApproveEndpointBase):
    """未知识别面: 404/404/422/已决重审 404。"""

    def test_unknown_command_hash_404(self):
        r = self._post(battle="battle-2", command_hash="f" * 64,
                       decision="approve")
        self.assertEqual(r.status_code, 404)
        self.assertIn("error", r.json())

    def test_unknown_battle_404(self):
        r = self._post(battle="battle-99", command_hash=H1, decision="approve")
        self.assertEqual(r.status_code, 404)
        self.assertIn("error", r.json())

    def test_bad_decision_422(self):
        r = self._post(battle="battle-2", command_hash=H1, decision="exempt")
        self.assertEqual(r.status_code, 422)
        self.assertIn("error", r.json())
        # 待审不动
        self.assertEqual(len(items_of(self.goal_dir)), 2)

    def test_already_decided_reapprove_404(self):
        r1 = self._post(battle="battle-2", command_hash=H1, decision="approve")
        self.assertEqual(r1.status_code, 200)
        r2 = self._post(battle="battle-2", command_hash=H1, decision="reject")
        self.assertEqual(r2.status_code, 404)          # 一次一决定不覆写
        rows, _s = _ap_rows(self.goal_dir)
        self.assertEqual(len(rows), 1)                 # 链上仍只一条


class TestBridgeFailureHonesty(ApproveEndpointBase):
    """桥失败 502 不造假: rc!=0 / 回执 ok 但读回未消项。"""

    def test_bridge_nonzero_rc_502_pending_unchanged(self):
        cp = subprocess.CompletedProcess([], 2, stdout=json.dumps(
            {"ok": False, "error": "command_hash 不在待审队列"}),
            stderr="")
        with mock.patch.object(approvals_router.subprocess, "run",
                               return_value=cp):
            r = self._post(battle="battle-2", command_hash=H1,
                           decision="approve")
        self.assertEqual(r.status_code, 502)
        self.assertIn("error", r.json())
        self.assertEqual(len(items_of(self.goal_dir)), 2)   # 待审纹丝不动
        self.assertEqual(_ap_rows(self.goal_dir)[0], [])    # 链上零审批行

    def test_bridge_ok_receipt_but_readback_still_pending_502(self):
        cp = subprocess.CompletedProcess([], 0, stdout=json.dumps(
            {"ok": True, "approval_id": "AP-1-0001", "decision": "approved"}),
            stderr="")
        with mock.patch.object(approvals_router.subprocess, "run",
                               return_value=cp):
            r = self._post(battle="battle-2", command_hash=H1,
                           decision="approve")
        self.assertEqual(r.status_code, 502)                # 读写不一致如实报
        self.assertIn("error", r.json())

    def test_bridge_timeout_502_honest(self):
        def _boom(*_a, **_k):
            raise subprocess.TimeoutExpired(cmd="bridge", timeout=60)
        with mock.patch.object(approvals_router.subprocess, "run",
                               side_effect=_boom):
            r = self._post(battle="battle-2", command_hash=H1,
                           decision="approve")
        self.assertEqual(r.status_code, 502)
        self.assertIn("超时", r.json()["error"])
        self.assertEqual(len(items_of(self.goal_dir)), 2)


class TestBridgeApproveSubprocess(unittest.TestCase):
    """engine_bridge approve 真子进程(TANYIN_HOME 合成根,真落链于临时目录)。"""

    def setUp(self):
        self.home, self.goal_dir = mk_battle_home()
        self.addCleanup(shutil.rmtree, self.home, True)

    def _run(self, *args, **env_extra):
        env = dict(os.environ, TANYIN_HOME=self.home, **env_extra)
        return subprocess.run(
            [sys.executable, BRIDGE, "approve"] + list(args),
            capture_output=True, text=True, env=env, timeout=60)

    def _receipt(self, cp):
        return json.loads(cp.stdout.strip().splitlines()[-1])

    def test_approve_writes_chain_and_receipt(self):
        cp = self._run("--battle", "battle-2", "--command-hash", H1,
                       "--decision", "approved", "--note", "靶场演练")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        rc = self._receipt(cp)
        self.assertTrue(rc["ok"])
        self.assertEqual(rc["decision"], "approved")
        self.assertTrue(rc["approval_id"].startswith("AP-"))
        self.assertEqual(rc["command_hash"], H1)
        # 落链: approvals 行+timeline 事件+链完整
        rows, s = _ap_rows(self.goal_dir)
        self.assertEqual(len(rows), 1)
        i_note = TABLES["approvals.tsv"].index("note")
        self.assertIn(EV1, rows[0][i_note])
        self.assertIn("靶场演练", rows[0][i_note])
        ok, bad = s.verify_chain()
        self.assertTrue(ok, "链断裂于第 %d 行" % bad)
        # 已决出队: 桥侧同源读回(ledger_reader 单源)
        self.assertEqual([it["id"] for it in items_of(self.goal_dir)], [H2])

    def test_reject_decision_lands(self):
        cp = self._run("--battle", "battle-2", "--command-hash", H2,
                       "--decision", "rejected")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        rows, _s = _ap_rows(self.goal_dir)
        i_dec = TABLES["approvals.tsv"].index("decision")
        self.assertEqual(rows[0][i_dec], "rejected")

    def test_unknown_hash_rc2(self):
        cp = self._run("--battle", "battle-2", "--command-hash", "e" * 64,
                       "--decision", "approved")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("待审", cp.stdout + cp.stderr)

    def test_missing_args_rc2(self):
        cp = self._run("--battle", "battle-2", "--decision", "approved")
        self.assertEqual(cp.returncode, 2)

    def test_decision_vocabulary_rejected_rc2(self):
        cp = self._run("--battle", "battle-2", "--command-hash", H1,
                       "--decision", "exempted")
        self.assertEqual(cp.returncode, 2)
        self.assertEqual(_ap_rows(self.goal_dir)[0], [])   # 零写入

    def test_approval_key_env_auto_signs(self):
        cp = self._run("--battle", "battle-2", "--command-hash", H1,
                       "--decision", "approved",
                       TANYIN_APPROVAL_KEY="t8-test-key")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        rows, _s = _ap_rows(self.goal_dir)
        i_note = TABLES["approvals.tsv"].index("note")
        self.assertIn("sig=", rows[0][i_note])            # 持钥通道自动签发
        ok, bad = _ap_rows(self.goal_dir)[1].verify_chain()
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
