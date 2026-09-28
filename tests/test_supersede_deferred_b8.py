# -*- coding: utf-8 -*-
"""批次 8 T1+T2：supersede 命令面（M2：add-finding 同键 REJECT 后无命令可铸 dst——
死路）+deferred 复活臂（M3：_INTENT_ARROWS deferred 无出边，延后 intent 永久滞留）。
红=复现台账反例；绿=T1 --supersede 铸行+T2 deferred→pending 复活臂。
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
sys.path.insert(0, os.path.join(HERE, ".."))
from tests.test_write_cmds import Base, call, T, TS


class TestSupersede(Base):
    BASE = ["--intent-id=INT-g1-0002", "--title=订单接口越权读取v2", "--confidence=C1", "--impact=高",
            "--exploitation-status=verified", "--scope-check=in_scope",
            "--description-brief=未登录可读任意订单复测", "--reproducible-steps=curl -s https://shop.example/api/orders?id=2",
            "--affected-asset-id=AST-g1-0002", "--evidence-ids=EV-g1-0001",
            "--vuln-ref=CVE-2024-1234", "--timestamp=" + TS]
    FIRST = [a.replace("v2", "v1").replace("id=2", "id=1").replace("复测", "初测") for a in BASE]

    def test_supersede_flow(self):
        self.assert_ok(call("add-finding", self.gd, *self.FIRST))
        old_id = self.rows("findings.tsv")[-1][0]
        snap = self.snap()
        res = call("add-finding", self.gd, *(self.BASE + ["--supersede=" + old_id]))
        self.assert_ok(res)
        rows = self.rows("findings.tsv")
        si = T["findings.tsv"].index("status")
        old_latest = [r for r in rows if r[0] == old_id][-1]
        self.assertEqual(old_latest[si], "superseded")
        ti = T["findings.tsv"].index("title")
        new_rows = [r for r in rows if "v2" in r[ti]]
        self.assertEqual(len(new_rows), 1)
        new_id = new_rows[0][0]
        self.assertEqual(new_rows[0][si], "active")
        ei = T["edges.tsv"]
        es = [r for r in self.rows("edges.tsv") if r[ei.index("kind")] == "supersedes"
              and r[ei.index("source_id")] == old_id and r[ei.index("target_id")] == new_id]
        self.assertTrue(es, "edges.tsv 须落 kind=supersedes 边")
        tl = [l for l in open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8").read().splitlines() if "supersede-finding" in l]
        self.assertTrue(tl, "timeline 须落 supersede-finding 事件")
        self.assert_ledger_ok()

    def test_supersede_wrong_target_rejected(self):
        self.assert_ok(call("add-finding", self.gd, *self.FIRST))
        # 目标 FD 的 dedup_key 不同（换 vuln-ref 形成异键）→ 拒收
        snap = self.snap()
        args = [a for a in self.BASE if not a.startswith("--vuln-ref=")] + ["--vuln-ref=CVE-2024-5678", "--supersede=FD-g1-9999"]
        self.assert_rej(call("add-finding", self.gd, *args), snap, "supersede")


class TestDeferredRevive(Base):
    def test_deferred_to_pending(self):
        self.assert_ok(call("add-intent", self.gd, "--title=延后复核", "--engine=web-blackbox",
                            "--kind=deep-dive", "--origin=entity", "--budget-share=100;10;1",
                            "--timestamp=" + TS))
        iid = self.rows("intents.tsv")[-1][0]
        self.assert_ok(call("set-intent-status", self.gd, "--id=" + iid, "--status=deferred",
                            "--reason=等凭据", "--activation=creds.status;eq;active",
                            "--timestamp=" + TS))
        snap = self.snap()
        res = call("set-intent-status", self.gd, "--id=" + iid, "--status=pending",
                   "--reason=凭据已到手，复活", "--timestamp=" + TS)
        self.assert_ok(res)
        it = self.rows("intents.tsv")
        si = T["intents.tsv"].index("status")
        self.assertEqual([r for r in it if r[0] == iid][-1][si], "pending")
        ai = T["intents.tsv"].index("activation")
        self.assertEqual([r for r in it if r[0] == iid][-1][ai], "creds.status;eq;active")
        self.assert_ledger_ok()

    def test_deferred_revive_requires_reason(self):
        self.assert_ok(call("add-intent", self.gd, "--title=延后无理由", "--engine=web-blackbox",
                            "--kind=deep-dive", "--origin=entity", "--budget-share=100;10;1",
                            "--timestamp=" + TS))
        iid = self.rows("intents.tsv")[-1][0]
        self.assert_ok(call("set-intent-status", self.gd, "--id=" + iid, "--status=deferred",
                            "--reason=等窗口", "--activation=facts.kind;eq;info",
                            "--timestamp=" + TS))
        snap = self.snap()
        self.assert_rej(call("set-intent-status", self.gd, "--id=" + iid, "--status=pending",
                             "--timestamp=" + TS), snap, "reason")


if __name__ == "__main__":
    unittest.main()
