# -*- coding: utf-8 -*-
"""功能19补件·审批降噪闭环（approval-de-noise-v1）——钉测。

python3 -m unittest tests.test_approval_denoise -v
律：
  ④预授权白名单：goal 目录 preauth.tsv（无表头 TSV，列序对齐审批既有表族——
    id 前缀 PA-、schema_version 尾列）；白名单内=零打扰放行入账（走既有
    approve 通道 decision=exempted + note 含原事件文本——query_cmds._replay_status
    同判定即刻出队）；界外/高危/过期=不豁免永远问。
  ⑤超时保守：待审挂起超 N 分钟（goal 目录 approval.json 可配 timeout_min，
    缺省 30）→ 保守跳过该操作 + 记账（approve 通道 decision=rejected，
    approver=超时保守策略，note 含原事件）+ 通知（timeline approval-timeout 行）
    ——不卡战线。
  HMAC 兼容：TANYIN_APPROVAL_KEY 在场=approve 须 --sig（同式
    HMAC-SHA256(sha256(key), command_hash)——write_cmds._approval_sig 单源语义，
    server.py:140 同形复制先例）；本模块照签，既有 test_p0_approval_hmac 不破坏。
  写入单源：一切 approvals 写经 registry.lookup("approve")（goal 写锁包装执法
    链），不碰 write_cmds。设计权威 docs/design/2026-10-20-command-approval-design.md（补件二）。
"""
import hashlib
import hmac
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)

from ledger import core, preauth, query_cmds, timeline  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
ENV_KEY = "TANYIN_APPROVAL_KEY"
NOW = "2026-09-24T12:00:00Z"      # sweep 注入钟（确定性）

EV_READ = "exec http-get https://app.example.com/admin"
RV_READ = "revert-cache-clear --token=abc"
EV_DANGER = "hook deploy canary token=abc123"
RV_DANGER = "revert-canary --token=abc123"


def sig_of(chash, key):
    return hmac.new(hashlib.sha256(key.encode()).digest(),
                    chash.encode(), hashlib.sha256).hexdigest()


class Base(unittest.TestCase):
    """夹具：G-g1（合法链账本）+ 追加两条待试行（新鲜/陈旧）+ preauth.tsv。"""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d)
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)
        # 夹具自带的 add-goal 待审行核销掉（ reverted ），只留测试自铸行
        timeline.append_tl_locked(
            self.d, "2026-09-23T01:30:00Z", "revert:add-goal G-g1-0001",
            actor="总控", phase="P3")
        self._old_key = os.environ.get(ENV_KEY)
        os.environ.pop(ENV_KEY, None)
        self.addCleanup(self._restore_key)

    def _restore_key(self):
        if self._old_key is None:
            os.environ.pop(ENV_KEY, None)
        else:
            os.environ[ENV_KEY] = self._old_key

    def _pend(self, ts, ev, rv):
        timeline.append_tl_locked(self.d, ts, ev, actor="CLI", phase="P3",
                                  revert=rv)

    def _write_preauth(self, lines):
        with open(os.path.join(self.d, "preauth.tsv"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def status_of(self, ev):
        s = core.Session(self.d)
        for it in query_cmds._replay_status(s):
            if it["row"][3] == ev:
                return it["status"]
        return None

    def approvals_text(self):
        with open(os.path.join(self.d, "approvals.tsv"),
                  encoding="utf-8") as f:
            return f.read()


# ═══════════════════ ④ 预授权白名单 ═══════════════════

class TestPreauthMatch(Base):
    """匹配律：只读探测+界内+效期内；高危/界外/过期永不豁免。"""

    def _entry(self, **kw):
        e = dict(id="PA-t1-0001", op_class="read-probe",
                 param_constraint="scope=example.com",
                 valid_from="2026-09-24T00:00:00Z",
                 valid_until="2026-09-25T00:00:00Z",
                 approver="range-operator", note="")
        e.update(kw)
        return e

    def test_read_probe_in_scope_matches(self):
        e = self._entry()
        ok, why = preauth.match_entry(e, EV_READ, RV_READ, now=NOW)
        self.assertTrue(ok, why)
        self.assertIn("只读", why)

    def test_read_probe_out_of_scope_misses(self):
        e = self._entry(param_constraint="scope=other.com")
        ok, _ = preauth.match_entry(e, EV_READ, RV_READ, now=NOW)
        self.assertFalse(ok)

    def test_dangerous_verb_never_matches(self):
        e = self._entry(op_class="read-probe",
                        param_constraint="scope=example.com")
        ok, _ = preauth.match_entry(e, EV_DANGER, RV_DANGER, now=NOW)
        self.assertFalse(ok, "高危动词必须落问")

    def test_expired_window_misses(self):
        e = self._entry(valid_until="2026-09-23T00:00:00Z")
        ok, _ = preauth.match_entry(e, EV_READ, RV_READ, now=NOW)
        self.assertFalse(ok)

    def test_retry_same_within_max(self):
        e = self._entry(op_class="retry-same", param_constraint="max=2")
        ok, _ = preauth.match_entry(e, EV_READ, RV_READ, same_count=2, now=NOW)
        self.assertTrue(ok)

    def test_retry_same_over_max(self):
        e = self._entry(op_class="retry-same", param_constraint="max=2")
        ok, _ = preauth.match_entry(e, EV_READ, RV_READ, same_count=3, now=NOW)
        self.assertFalse(ok)

    def test_unknown_op_class_misses(self):
        e = self._entry(op_class="wild-thing")
        ok, _ = preauth.match_entry(e, EV_READ, RV_READ, now=NOW)
        self.assertFalse(ok)


class TestPreauthSweep(Base):
    """零打扰入账：白名单内即刻出队（既有 exempted 判定），走 approve 通道。"""

    def setUp(self):
        super().setUp()
        self._pend("2026-09-24T11:00:00Z", EV_READ, RV_READ)
        self._pend("2026-09-24T11:30:00Z", EV_DANGER, RV_DANGER)
        self._write_preauth([
            "PA-t1-0001\tread-probe\tscope=example.com\t"
            "2026-09-24T00:00:00Z\t2026-09-25T00:00:00Z\t"
            "range-operator\t界内只读探测免打扰\t2",
        ])

    def test_sweep_exempts_whitelisted_only(self):
        out = preauth.sweep(self.d, now=NOW)
        self.assertEqual([e["event"] for e in out["exempted"]], [EV_READ])
        self.assertEqual(out["exempted"][0]["preauth_id"], "PA-t1-0001")
        self.assertEqual(self.status_of(EV_READ), "exempted")   # 出队
        self.assertEqual(self.status_of(EV_DANGER), "pending")  # 高危永远问
        self.assertIn("exempted", self.approvals_text())        # 入账
        self.assertIn(EV_READ, self.approvals_text())           # note 含原事件

    def test_sweep_approver_is_whitelist(self):
        preauth.sweep(self.d, now=NOW)
        rows = core.Session(self.d).rows("approvals.tsv")
        newest = [r for r in rows if r[2] == "exempted"][-1]
        self.assertIn("预授权", newest[3])

    def test_sweep_no_preauth_file_noop(self):
        os.remove(os.path.join(self.d, "preauth.tsv"))
        out = preauth.sweep(self.d, now=NOW)
        self.assertEqual(out["exempted"], [])
        self.assertEqual(self.status_of(EV_READ), "pending")

    def test_sweep_with_hmac_key_signs(self):
        key = "test-key-denoise"
        os.environ[ENV_KEY] = key
        out = preauth.sweep(self.d, now=NOW)
        self.assertEqual(len(out["exempted"]), 1)
        rows = core.Session(self.d).rows("approvals.tsv")
        ex = [r for r in rows if r[2] == "exempted"][-1]
        chash = hashlib.sha256(RV_READ.encode()).hexdigest()
        want = "sig=" + sig_of(chash, key)
        self.assertIn(want, ex[5], "豁免行须带同式 HMAC 签名段")

    def test_sweep_not_duplicated(self):
        preauth.sweep(self.d, now=NOW)
        out2 = preauth.sweep(self.d, now=NOW)
        self.assertEqual(out2["exempted"], [], "已豁免不重复入账")


# ═══════════════════ ⑤ 超时保守 ═══════════════════

class TestTimeoutSweep(Base):

    def setUp(self):
        super().setUp()
        # 陈旧行（2h 前）+ 新鲜行（5min 前）；sweep 钟=NOW
        self._pend("2026-09-24T10:00:00Z", EV_DANGER, RV_DANGER)
        self._pend("2026-09-24T11:55:00Z", EV_READ, RV_READ)

    def test_timeout_old_pending_skipped_and_accounted(self):
        out = preauth.sweep(self.d, now=NOW, timeout_min=30)
        self.assertEqual([e["event"] for e in out["timed_out"]], [EV_DANGER])
        rows = core.Session(self.d).rows("approvals.tsv")
        rj = [r for r in rows if r[2] == "rejected"][-1]
        self.assertIn("超时保守", rj[3])
        self.assertIn(EV_DANGER, rj[5])               # note 含原事件=可对账
        tl = core.Session(self.d).rows("timeline.tsv")
        self.assertTrue(any(x[3].startswith("approval-timeout") for x in tl),
                        "须落通知行")
        self.assertEqual(self.status_of(EV_READ), "pending")  # 新鲜不动

    def test_timeout_fresh_untouched(self):
        out = preauth.sweep(self.d, now=NOW, timeout_min=180)  # 帽 3h：都不老
        self.assertEqual(out["timed_out"], [])
        self.assertEqual(self.status_of(EV_DANGER), "pending")

    def test_timeout_default_30(self):
        out = preauth.sweep(self.d, now=NOW)          # 缺省 30 分钟
        self.assertEqual([e["event"] for e in out["timed_out"]], [EV_DANGER])
        waited = out["timed_out"][0]["waited_min"]
        self.assertGreaterEqual(waited, 120)

    def test_timeout_configurable_via_goal_file(self):
        with open(os.path.join(self.d, "approval.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"timeout_min": 10}')
        # 11:55 行距今 5min <10 不动；10:00 行 120min>10 跳过
        out = preauth.sweep(self.d, now=NOW)
        self.assertEqual([e["event"] for e in out["timed_out"]], [EV_DANGER])

    def test_timeout_with_hmac_key_signs(self):
        key = "test-key-timeout"
        os.environ[ENV_KEY] = key
        out = preauth.sweep(self.d, now=NOW)
        self.assertEqual(len(out["timed_out"]), 1)
        rows = core.Session(self.d).rows("approvals.tsv")
        rj = [r for r in rows if r[2] == "rejected"][-1]
        chash = hashlib.sha256(RV_DANGER.encode()).hexdigest()
        self.assertIn("sig=" + sig_of(chash, key), rj[5])

    def test_combined_preauth_wins_over_timeout(self):
        """白名单内且陈旧：先豁免（零打扰），不落超时拒绝。"""
        self._pend("2026-09-24T09:00:00Z", EV_READ + " old", RV_READ)
        self._write_preauth([
            "PA-t1-0001\tread-probe\tscope=example.com\t"
            "2026-09-24T00:00:00Z\t2026-09-25T00:00:00Z\t"
            "range-operator\t界内只读免打扰\t2",
        ])
        out = preauth.sweep(self.d, now=NOW, timeout_min=30)
        self.assertIn(EV_READ + " old", [e["event"] for e in out["exempted"]])
        self.assertNotIn(EV_READ + " old",
                         [e["event"] for e in out["timed_out"]])


# ═══════════════════ 格式对齐与表律 ═══════════════════

class TestFormatAlignment(unittest.TestCase):

    def test_preauth_columns_pinned(self):
        """列序钉死（操作类+参数约束+有效期——对齐审批表族：无表头/尾版本列）。"""
        self.assertEqual(preauth.COLS,
                         ("id", "op_class", "param_constraint",
                          "valid_from", "valid_until", "approver", "note",
                          "schema_version"))

    def test_read_preauth_missing_file_empty(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        self.assertEqual(preauth.read_preauth(d), [])

    def test_read_preauth_parses_rows(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        with open(os.path.join(d, "preauth.tsv"), "w",
                  encoding="utf-8") as f:
            f.write("PA-1\tread-probe\tscope=a.com\t2026-01-01T00:00:00Z\t"
                    "2026-02-01T00:00:00Z\top\t说明\t2\n\n")
        rows = preauth.read_preauth(d)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["op_class"], "read-probe")
        self.assertEqual(rows[0]["param_constraint"], "scope=a.com")


if __name__ == "__main__":
    unittest.main()
