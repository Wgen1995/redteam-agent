# -*- coding: utf-8 -*-
"""批次 1 T3-T6 写命令组测试（19 条）——python3 -m unittest tests.test_write_cmds
范式：临时目录拷贝 tests/fixtures/G-g1 起底（不动夹具本体）；虚构数据仅 .example；
每命令 ≥1 正例 + ≥1 拒收例（拒收后断言 13 表 TSV 字节不变）。
"""
import hashlib, io, os, shutil, subprocess, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import core, write_cmds

FIX = os.path.join(HERE, "fixtures", "G-g1")
T = core.TABLES
TS = "2026-09-23T12:00:00Z"
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
ALL_TABLES = list(T.keys())


def snapshot(gd):
    snap = {}
    for t in ALL_TABLES:
        p = os.path.join(gd, t)
        snap[t] = open(p, "rb").read() if os.path.exists(p) else None
    return snap


def unchanged(gd, snap):
    for t, b in snap.items():
        p = os.path.join(gd, t)
        cur = open(p, "rb").read() if os.path.exists(p) else None
        if cur != b:
            return False, t
    return True, None


def call(name, gd, *args):
    buf_o, buf_e = io.StringIO(), io.StringIO()
    with redirect_stdout(buf_o), redirect_stderr(buf_e):
        code = write_cmds.HANDLERS[name](gd, list(args))
    return code, buf_o.getvalue(), buf_e.getvalue()


def read(gd, t):
    p = os.path.join(gd, t)
    return core.read_tsv(p, len(T[t])) if os.path.exists(p) else []


def write(gd, t, rows):
    core.write_tsv(os.path.join(gd, t), rows)


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def snap(self):
        return snapshot(self.gd)

    def rows(self, t):
        return read(self.gd, t)

    def n_tl(self):
        return len(self.rows("timeline.tsv"))

    def assert_ok(self, res):
        self.assertEqual(res[0], 0, "exit!=0 out=%s err=%s" % (res[1], res[2]))
        self.assertTrue(res[1].startswith("OK"), res[1])

    def assert_rej(self, res, snap, why_in="", gd=None):
        self.assertEqual(res[0], 1, "exit!=1 out=%s err=%s" % (res[1], res[2]))
        self.assertTrue(res[2].startswith("REJECT"), res[2])
        if why_in:
            self.assertIn(why_in, res[2])
        same, t = unchanged(gd or self.gd, snap)
        self.assertTrue(same, "拒收后表被改动: " + str(t))

    def assert_ledger_ok(self, gd=None):
        s = core.Session(gd or self.gd)
        self.assertEqual(s.validate(), [])

    def fresh_dir(self, name="G-g2"):
        d = os.path.join(self.td.name, name)
        os.makedirs(d, exist_ok=True)
        return d


class TestAddGoal(Base):
    ARGS = ["--target=shop2.example", "--objective=授权测试", "--auth-doc=auth/a.pdf",
            "--auth-sha256=" + "a" * 64, "--signer=client-cso", "--valid-from=2026-09-01",
            "--valid-until=2026-09-30", "--budget=2M;50000;40", "--model-tier=strong",
            "--guard-tier=T3", "--timestamp=" + TS]

    def test_positive_fresh_dir(self):
        gd = self.fresh_dir()
        before = self.n_tl() if os.path.exists(os.path.join(gd, "timeline.tsv")) else 0
        res = call("add-goal", gd, *self.ARGS)
        self.assert_ok(res)
        g = read(gd, "goals.tsv")
        self.assertEqual(len(g), 1)
        self.assertEqual(len(g[0]), len(T["goals.tsv"]))
        self.assertEqual(g[0][0], "G-g2-0001")
        self.assertEqual(g[0][T["goals.tsv"].index("schema_version")], "2")
        self.assertEqual(len(read(gd, "timeline.tsv")), before + 1)
        self.assert_ledger_ok(gd)

    def test_reject_fixture_already_has_goal(self):
        snap = self.snap()
        res = call("add-goal", self.gd, *self.ARGS)
        self.assert_rej(res, snap)

    def test_reject_empty_signer(self):
        gd = self.fresh_dir()
        snap = snapshot(gd)
        args = [a for a in self.ARGS if not a.startswith("--signer=")] + ["--signer="]
        res = call("add-goal", gd, *args)
        self.assert_rej(res, snap, gd=gd)

    def test_reject_bad_budget_and_tiers_and_window(self):
        gd = self.fresh_dir()
        snap = snapshot(gd)
        bad = [a for a in self.ARGS if not a.startswith("--budget=")] + ["--budget=2M;50000"]
        self.assert_rej(call("add-goal", gd, *bad), snapshot(gd), gd=gd)
        bad = [a for a in self.ARGS if not a.startswith("--model-tier=")] + ["--model-tier=high"]
        self.assert_rej(call("add-goal", gd, *bad), snapshot(gd), gd=gd)
        bad = [a for a in self.ARGS if not a.startswith("--guard-tier=")] + ["--guard-tier=T9"]
        self.assert_rej(call("add-goal", gd, *bad), snapshot(gd), gd=gd)
        bad = [a for a in self.ARGS if not a.startswith("--valid-until=")] + ["--valid-until=2026-08-31"]
        self.assert_rej(call("add-goal", gd, *bad), snapshot(gd), gd=gd)
        self.assertTrue(unchanged(gd, snap)[0])

    def test_reject_tier0_not_for_add_goal(self):
        # add-goal 豁免 Tier0（空目录可立项）——反证其他命令被 Tier0 拒（见 TestTier0）
        gd = self.fresh_dir()
        res = call("add-goal", gd, *self.ARGS)
        self.assertEqual(res[0], 0)


class TestAddScope(Base):
    def test_positive_include(self):
        before = self.n_tl()
        res = call("add-scope", self.gd, "--kind=include", "--matcher=api.shop.example",
                   "--note=API 域", "--timestamp=" + TS)
        self.assert_ok(res)
        sc = self.rows("scope.tsv")
        self.assertEqual(sc[-1][0], "S-g1-0003")
        self.assertEqual(len(sc[-1]), len(T["scope.tsv"]))
        self.assertEqual(sc[-1][T["scope.tsv"].index("amendment_of")], "")
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_positive_account_grant(self):
        res = call("add-scope", self.gd, "--kind=account-grant", "--matcher=shop.example",
                   "--account=admin;operator", "--permitted-actions=read;probe", "--timestamp=" + TS)
        self.assert_ok(res)

    def test_reject_bad_kind(self):
        snap = self.snap()
        res = call("add-scope", self.gd, "--kind=whitelist", "--matcher=a.example", "--timestamp=" + TS)
        self.assert_rej(res, snap)

    def test_reject_account_grant_missing_account(self):
        snap = self.snap()
        res = call("add-scope", self.gd, "--kind=account-grant", "--matcher=a.example",
                   "--permitted-actions=read", "--timestamp=" + TS)
        self.assert_rej(res, snap)

    def test_reject_bad_matcher(self):
        snap = self.snap()
        res = call("add-scope", self.gd, "--kind=include", "--matcher=not a matcher!", "--timestamp=" + TS)
        self.assert_rej(res, snap, "matcher")

    def test_reject_cidr_form(self):
        snap = self.snap()
        self.assert_rej(call("add-scope", self.gd, "--kind=include", "--matcher=10.10.0.0/99",
                             "--timestamp=" + TS), snap)
        res = call("add-scope", self.gd, "--kind=include", "--matcher=10.20.0.0/16", "--timestamp=" + TS)
        self.assert_ok(res)

    def test_reject_account_cred_ref_unclosed(self):
        snap = self.snap()
        res = call("add-scope", self.gd, "--kind=account-grant", "--matcher=a.example",
                   "--account=CRED-g1-0009", "--permitted-actions=read", "--timestamp=" + TS)
        self.assert_rej(res, snap)


class TestAddIntent(Base):
    BASE = ["--title=越权读取订单", "--engine=web-blackbox", "--kind=deep-dive",
            "--origin=entity", "--budget-share=1000;50;2", "--timestamp=" + TS]

    def test_positive_candidate(self):
        before = self.n_tl()
        res = call("add-intent", self.gd, *self.BASE)
        self.assert_ok(res)
        it = self.rows("intents.tsv")
        self.assertEqual(it[-1][0], "INT-g1-0003")
        self.assertEqual(len(it[-1]), len(T["intents.tsv"]))
        self.assertEqual(it[-1][T["intents.tsv"].index("status")], "candidate")
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_positive_recon_event_pending(self):
        res = call("add-intent", self.gd, "--title=新资产测绘", "--engine=recon", "--kind=recon",
                   "--origin=recon-event", "--budget-share=100;10;1", "--timestamp=" + TS)
        self.assert_ok(res)
        self.assertEqual(self.rows("intents.tsv")[-1][T["intents.tsv"].index("status")], "pending")

    def test_reject_dedup(self):
        self.assert_ok(call("add-intent", self.gd, *self.BASE))
        snap = self.snap()
        self.assert_rej(call("add-intent", self.gd, *self.BASE), snap, "dedup")

    def test_reject_bad_kind_origin_share(self):
        snap = self.snap()
        bad = [a for a in self.BASE if not a.startswith("--kind=")] + ["--kind=exploit"]
        self.assert_rej(call("add-intent", self.gd, *bad), snapshot(self.gd))
        bad = [a for a in self.BASE if not a.startswith("--origin=")] + ["--origin=god"]
        self.assert_rej(call("add-intent", self.gd, *bad), snapshot(self.gd))
        bad = [a for a in self.BASE if not a.startswith("--budget-share=")] + ["--budget-share=100"]
        self.assert_rej(call("add-intent", self.gd, *bad), snapshot(self.gd))
        self.assertTrue(unchanged(self.gd, snap)[0])

    def test_authz_diff_cred_gate(self):
        snap = self.snap()
        base = ["--title=身份矩阵差分", "--engine=differential", "--kind=authz-diff",
                "--origin=entity", "--budget-share=100;10;1", "--timestamp=" + TS]
        self.assert_rej(call("add-intent", self.gd, *base), snap, "cred")
        self.assert_rej(call("add-intent", self.gd, *(base + ["--cred=CRED-g1-0009"])), snapshot(self.gd))
        self.assert_rej(call("add-intent", self.gd, *(base + ["--cred=CRED-g1-0001", "--actions=delete"])),
                        snapshot(self.gd), "permitted_actions")
        self.assert_ok(call("add-intent", self.gd, *(base + ["--cred=CRED-g1-0001", "--actions=read;probe"])))

    def test_reject_out_of_scope_asset(self):
        self.assert_ok(call("add-asset", self.gd, "--type=subdomain", "--value=evil.example",
                            "--timestamp=" + TS))
        ast = self.rows("assets.tsv")
        oos = [r[0] for r in ast if r[T["assets.tsv"].index("in_scope")] == "out_of_scope"]
        self.assertTrue(oos, "界外资产应自动标 out_of_scope 且不拒收")
        snap = self.snap()
        res = call("add-intent", self.gd, "--title=界外派生", "--engine=recon", "--kind=recon",
                   "--origin=entity", "--budget-share=10;1;1", "--asset=" + oos[0], "--timestamp=" + TS)
        self.assert_rej(res, snap, "界外")


class TestSetIntentStatus(Base):
    def test_positive_pending_to_active(self):
        before = self.n_tl()
        res = call("set-intent-status", self.gd, "--id=INT-g1-0002", "--status=active", "--timestamp=" + TS)
        self.assert_ok(res)
        it = [r for r in self.rows("intents.tsv") if r[0] == "INT-g1-0002"]
        self.assertEqual(it[-1][T["intents.tsv"].index("status")], "active")
        self.assertEqual(len(it), 2)
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_reject_off_machine(self):
        snap = self.snap()
        self.assert_rej(call("set-intent-status", self.gd, "--id=INT-g1-0001", "--status=active",
                             "--timestamp=" + TS), snap, "状态机")
        self.assert_rej(call("set-intent-status", self.gd, "--id=INT-g1-0002", "--status=rejected",
                             "--timestamp=" + TS), snapshot(self.gd), "状态机")

    def _mk_candidate(self):
        self.assert_ok(call("add-intent", self.gd, "--title=待定假设", "--engine=kb",
                            "--kind=deep-dive", "--origin=llm", "--budget-share=10;1;1",
                            "--timestamp=" + TS))
        return self.rows("intents.tsv")[-1][0]

    def test_reject_reason_required(self):
        iid = self._mk_candidate()
        snap = self.snap()
        res = call("set-intent-status", self.gd, "--id=" + iid, "--status=deferred",
                   "--activation=cred;eq;CRED-g1-0001", "--timestamp=" + TS)
        self.assert_rej(res, snap, "reason")

    def test_deferred_activation(self):
        iid = self._mk_candidate()
        snap = self.snap()
        res = call("set-intent-status", self.gd, "--id=" + iid, "--status=deferred",
                   "--reason=等凭据", "--activation=cred;eq", "--timestamp=" + TS)
        self.assert_rej(res, snap, "activation")
        res = call("set-intent-status", self.gd, "--id=" + iid, "--status=deferred",
                   "--reason=等凭据", "--activation=cred;eq;CRED-g1-0001", "--timestamp=" + TS)
        self.assert_ok(res)

    def test_blocked_revival_needs_approval(self):
        self.assert_ok(call("set-intent-status", self.gd, "--id=INT-g1-0002", "--status=active",
                            "--timestamp=" + TS))
        self.assert_ok(call("set-intent-status", self.gd, "--id=INT-g1-0002", "--status=blocked",
                            "--reason=会话过期", "--timestamp=" + TS))
        snap = self.snap()
        self.assert_rej(call("set-intent-status", self.gd, "--id=INT-g1-0002", "--status=active",
                             "--timestamp=" + TS), snap, "approval")
        self.assert_ok(call("set-intent-status", self.gd, "--id=INT-g1-0002", "--status=active",
                            "--approval=AP-g1-0001", "--timestamp=" + TS))

    def test_reject_unknown_id(self):
        snap = self.snap()
        self.assert_rej(call("set-intent-status", self.gd, "--id=INT-g1-0099", "--status=active",
                             "--timestamp=" + TS), snap)


class TestAddFact(Base):
    def test_positive(self):
        before = self.n_tl()
        res = call("add-fact", self.gd, "--intent-id=INT-g1-0001", "--kind=port",
                   "--target=10.10.1.5", "--detail=443/tcp open", "--confidence=0.9", "--timestamp=" + TS)
        self.assert_ok(res)
        f = self.rows("facts.tsv")
        self.assertEqual(f[-1][0], "F-g1-0003")
        self.assertEqual(len(f[-1]), len(T["facts.tsv"]))
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_reject_redact(self):
        snap = self.snap()
        res = call("add-fact", self.gd, "--intent-id=INT-g1-0001", "--kind=http",
                   "--target=admin-internal.shop.example", "--detail=password=Sup3rS3cret!",
                   "--confidence=0.9", "--timestamp=" + TS)
        self.assert_rej(res, snap, "redact")

    def test_reject_confidence_and_ref(self):
        snap = self.snap()
        self.assert_rej(call("add-fact", self.gd, "--intent-id=INT-g1-0001", "--kind=port",
                             "--target=a.example", "--detail=x", "--confidence=1.5",
                             "--timestamp=" + TS), snapshot(self.gd))
        self.assert_rej(call("add-fact", self.gd, "--intent-id=INT-g1-0099", "--kind=port",
                             "--target=a.example", "--detail=x", "--confidence=0.5",
                             "--timestamp=" + TS), snapshot(self.gd))
        self.assert_rej(call("add-fact", self.gd, "--intent-id=INT-g1-0001", "--kind=backdoor",
                             "--target=a.example", "--detail=x", "--confidence=0.5",
                             "--timestamp=" + TS), snapshot(self.gd))
        self.assertTrue(unchanged(self.gd, snap)[0])

    def test_escape_roundtrip(self):
        detail = "a\tb\\c;d" + chr(10) + "e"
        res = call("add-fact", self.gd, "--intent-id=INT-g1-0001", "--kind=info",
                   "--target=x.example", "--detail=" + detail, "--confidence=0.5", "--timestamp=" + TS)
        self.assert_ok(res)
        raw = open(os.path.join(self.gd, "facts.tsv"), "rb").read().decode("utf-8")
        last_line = raw.rstrip(chr(10)).split(chr(10))[-1]
        cells = last_line.split(chr(9))
        self.assertEqual(len(cells), len(T["facts.tsv"]))
        self.assertIn("a\\tb", cells[4])
        self.assertNotIn(chr(10), last_line.replace("\\n", ""))
        self.assertEqual(self.rows("facts.tsv")[-1][T["facts.tsv"].index("detail")], detail)
        self.assert_ledger_ok()


class TestAddFinding(Base):
    BASE = ["--intent-id=INT-g1-0002", "--title=订单接口越权读取", "--confidence=C1", "--impact=高",
            "--exploitation-status=verified", "--scope-check=in_scope",
            "--description-brief=未登录可读任意订单", "--reproducible-steps=curl -s https://shop.example/api/orders?id=1",
            "--affected-asset-id=AST-g1-0002", "--evidence-ids=EV-g1-0001",
            "--vuln-ref=CVE-2024-1234", "--timestamp=" + TS]

    def test_positive(self):
        before = self.n_tl()
        res = call("add-finding", self.gd, *self.BASE)
        self.assert_ok(res)
        fd = self.rows("findings.tsv")
        self.assertEqual(fd[-1][0], "FD-g1-0002")
        self.assertEqual(len(fd[-1]), len(T["findings.tsv"]))
        self.assertEqual(fd[-1][T["findings.tsv"].index("status")], "active")
        card = os.path.join(self.gd, "findings-cards", "FD-g1-0002.md")
        self.assertTrue(os.path.exists(card))
        self.assertIn("dedup_key: " + fd[-1][T["findings.tsv"].index("dedup_key")],
                      open(card, encoding="utf-8").read())
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_reject_no_repro_steps(self):
        snap = self.snap()
        args = [a for a in self.BASE if not a.startswith("--reproducible-steps=")] + ["--reproducible-steps="]
        self.assert_rej(call("add-finding", self.gd, *args), snap, "reproducible")

    def test_reject_dedup_active(self):
        self.assert_ok(call("add-finding", self.gd, *self.BASE))
        snap = self.snap()
        self.assert_rej(call("add-finding", self.gd, *self.BASE), snap, "supersede")

    def test_reject_c2_without_evidence(self):
        snap = self.snap()
        args = [a for a in self.BASE if not a.startswith("--confidence=")]
        args = [a for a in args if not a.startswith("--evidence-ids=")] + ["--confidence=C2"]
        self.assert_rej(call("add-finding", self.gd, *args), snapshot(self.gd), "C2")

    def test_reject_enums_refs_vulnref_brief(self):
        base2 = list(self.BASE)
        def rej(extra):
            snap = self.snap()
            self.assert_rej(call("add-finding", self.gd, *extra), snap)
        rej([a for a in base2 if not a.startswith("--impact=")] + ["--impact=critical"])
        rej([a for a in base2 if not a.startswith("--exploitation-status=")] + ["--exploitation-status=maybe"])
        rej([a for a in base2 if not a.startswith("--scope-check=")] + ["--scope-check=unknown"]) 
        rej([a for a in base2 if not a.startswith("--affected-asset-id=")] + ["--affected-asset-id=AST-g1-0099"])
        rej([a for a in base2 if not a.startswith("--evidence-ids=")] + ["--evidence-ids=EV-g1-0099"])
        rej([a for a in base2 if not a.startswith("--auth-context=")] + ["--auth-context=CRED-g1-0099"])
        rej([a for a in base2 if not a.startswith("--vuln-ref=")] + ["--vuln-ref=OSV-123"])
        rej([a for a in base2 if not a.startswith("--description-brief=")] + ["--description-brief=" + "长" * 201])


class TestSupersedeFinding(Base):
    def craft(self, same_key=True, source_active=True):
        rows = self.rows("findings.tsv")
        fi = T["findings.tsv"].index
        rows[0][fi("status")] = "active" if source_active else "superseded"
        key = rows[0][fi("dedup_key")]
        r2 = list(rows[0])
        r2[0] = "FD-g1-0002"
        r2[fi("dedup_key")] = key if same_key else key + "-x"
        rows.append(r2)
        write(self.gd, "findings.tsv", rows)

    def test_positive(self):
        self.craft()
        before = self.n_tl()
        res = call("supersede-finding", self.gd, "--id=FD-g1-0001", "--superseded-by=FD-g1-0002",
                   "--timestamp=" + TS)
        self.assert_ok(res)
        fd = self.rows("findings.tsv")
        tomb = [r for r in fd if r[0] == "FD-g1-0001"]
        self.assertEqual(tomb[-1][T["findings.tsv"].index("status")], "superseded")
        eg = self.rows("edges.tsv")
        self.assertEqual(eg[-1][T["edges.tsv"].index("kind")], "supersedes")
        self.assertEqual(eg[-1][T["edges.tsv"].index("source_id")], "FD-g1-0001")
        self.assertEqual(eg[-1][T["edges.tsv"].index("target_id")], "FD-g1-0002")
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_reject_cross_key(self):
        self.craft(same_key=False)
        snap = self.snap()
        self.assert_rej(call("supersede-finding", self.gd, "--id=FD-g1-0001",
                             "--superseded-by=FD-g1-0002", "--timestamp=" + TS), snap, "dedup_key")

    def test_reject_source_not_active_and_refs(self):
        self.craft(source_active=False)
        snap = self.snap()
        self.assert_rej(call("supersede-finding", self.gd, "--id=FD-g1-0001",
                             "--superseded-by=FD-g1-0002", "--timestamp=" + TS), snap, "active")
        self.assert_rej(call("supersede-finding", self.gd, "--id=FD-g1-0099",
                             "--superseded-by=FD-g1-0002", "--timestamp=" + TS), snapshot(self.gd))
        self.assert_rej(call("supersede-finding", self.gd, "--id=FD-g1-0002",
                             "--superseded-by=FD-g1-0002", "--timestamp=" + TS), snapshot(self.gd))


class TestAddAsset(Base):
    def test_positive_in_scope(self):
        before = self.n_tl()
        res = call("add-asset", self.gd, "--type=subdomain", "--value=cdn.shop.example",
                   "--meta=CDN", "--timestamp=" + TS)
        self.assert_ok(res)
        a = self.rows("assets.tsv")
        self.assertEqual(a[-1][0], "AST-g1-0004")
        self.assertEqual(len(a[-1]), len(T["assets.tsv"]))
        self.assertEqual(a[-1][T["assets.tsv"].index("in_scope")], "in_scope")
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_positive_out_of_scope_not_rejected(self):
        res = call("add-asset", self.gd, "--type=subdomain", "--value=evil.example", "--timestamp=" + TS)
        self.assert_ok(res)
        self.assertEqual(self.rows("assets.tsv")[-1][T["assets.tsv"].index("in_scope")], "out_of_scope")

    def test_reject_pivot_and_dup_and_enum(self):
        snap = self.snap()
        self.assert_rej(call("add-asset", self.gd, "--type=pivot", "--value=10.10.9.9",
                             "--timestamp=" + TS), snap, "批次 4")
        self.assert_ok(call("add-asset", self.gd, "--type=subdomain", "--value=dev.shop.example",
                            "--timestamp=" + TS))
        self.assert_rej(call("add-asset", self.gd, "--type=subdomain", "--value=dev.shop.example",
                             "--timestamp=" + TS), self.snap(), "重复")
        self.assert_rej(call("add-asset", self.gd, "--type=botnet", "--value=x.example",
                             "--timestamp=" + TS), self.snap())


class TestAddEdge(Base):
    def test_positive(self):
        before = self.n_tl()
        res = call("add-edge", self.gd, "--kind=spawns", "--source-id=G-g1-0001",
                   "--target-id=INT-g1-0002", "--provenance=P3", "--timestamp=" + TS)
        self.assert_ok(res)
        e = self.rows("edges.tsv")
        self.assertEqual(e[-1][0], "E-g1-0003")
        self.assertEqual(len(e[-1]), len(T["edges.tsv"]))
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_reject_direction_kind_dup_ref(self):
        snap = self.snap()
        self.assert_rej(call("add-edge", self.gd, "--kind=spawns", "--source-id=INT-g1-0001",
                             "--target-id=G-g1-0001", "--provenance=x", "--timestamp=" + TS), snap, "方向")
        self.assert_rej(call("add-edge", self.gd, "--kind=hyper", "--source-id=G-g1-0001",
                             "--target-id=INT-g1-0002", "--provenance=x", "--timestamp=" + TS), snapshot(self.gd))
        self.assert_rej(call("add-edge", self.gd, "--kind=spawns", "--source-id=G-g1-0001",
                             "--target-id=INT-g1-0001", "--provenance=x", "--timestamp=" + TS),
                        snapshot(self.gd), "重复")
        self.assert_rej(call("add-edge", self.gd, "--kind=proves", "--source-id=INT-g1-0001",
                             "--target-id=FD-g1-0099", "--provenance=x", "--timestamp=" + TS), snapshot(self.gd))

    def test_positive_evidences_and_crossref(self):
        self.assert_ok(call("add-edge", self.gd, "--kind=evidences", "--source-id=FD-g1-0001",
                            "--target-id=EV-g1-0001", "--provenance=P3", "--timestamp=" + TS))
        self.assert_ok(call("add-edge", self.gd, "--kind=cross_ref", "--source-id=INT-g1-0001",
                            "--target-id=F-g1-0001", "--provenance=P3", "--timestamp=" + TS))


class TestAddEvidence(Base):
    ART = "evidence/artifact.raw"
    CONTENT = b"HTTP/1.1 200 OK\nContent-Type: application/json\n{\"ok\":true}\n"

    def setUp(self):
        super().setUp()
        p = os.path.join(self.gd, self.ART)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").write(self.CONTENT)

    def test_positive(self):
        before = self.n_tl()
        res = call("add-evidence", self.gd, "--title=订单接口响应", "--source-type=command",
                   "--observed-at=" + TS, "--network-position=internet",
                   "--repro-command=curl -s -H X-Auth:{{vault:cred-1}} https://shop.example/api/orders",
                   "--repro-kind=single", "--artifact=" + self.ART, "--raw-excerpt=200 OK ok:true",
                   "--linked-finding=FD-g1-0001", "--pair-group=PG-g1-0002", "--timestamp=" + TS)
        self.assert_ok(res)
        ev = self.rows("E-index.tsv")
        self.assertEqual(ev[-1][0], "EV-g1-0002")
        self.assertEqual(len(ev[-1]), len(T["E-index.tsv"]))
        self.assertEqual(ev[-1][T["E-index.tsv"].index("content_hash_raw")],
                         hashlib.sha256(self.CONTENT).hexdigest())
        self.assertTrue(os.path.exists(os.path.join(self.gd, "evidence", "EV-g1-0002.md")))
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_reject_redact_repro(self):
        snap = self.snap()
        res = call("add-evidence", self.gd, "--title=x", "--source-type=command",
                   "--observed-at=" + TS, "--network-position=internet",
                   "--repro-command=curl -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sig.part' https://a.example",
                   "--repro-kind=single", "--artifact=" + self.ART, "--timestamp=" + TS)
        self.assert_rej(res, snap, "redact")

    def test_reject_artifact_dup(self):
        args = ["--title=x", "--source-type=file", "--observed-at=" + TS, "--network-position=intranet",
                "--repro-command=cat " + self.ART, "--repro-kind=single", "--artifact=" + self.ART,
                "--timestamp=" + TS]
        self.assert_ok(call("add-evidence", self.gd, *args))
        self.assert_rej(call("add-evidence", self.gd, *args), self.snap(), "只增不覆盖")

    def test_reject_enums_and_ref(self):
        base = ["--title=x", "--source-type=manual", "--observed-at=" + TS, "--network-position=vpn",
                "--repro-command=echo hi", "--repro-kind=once", "--artifact=evidence/x.raw",
                "--timestamp=" + TS]
        snap = self.snap()
        self.assert_rej(call("add-evidence", self.gd, *base), snap)
        base = [a if not a.startswith("--network-position=") else "--network-position=same-host" for a in base]
        base = [a if not a.startswith("--repro-kind=") else "--repro-kind=concurrent" for a in base]
        base.append("--linked-finding=FD-g1-0099")
        self.assert_rej(call("add-evidence", self.gd, *base), snapshot(self.gd))

    def test_positive_jumphost(self):
        res = call("add-evidence", self.gd, "--title=x", "--source-type=capture",
                   "--observed-at=" + TS, "--network-position=jumphost:bastion-1",
                   "--repro-command=echo hi", "--repro-kind=single",
                   "--artifact=evidence/y.raw", "--timestamp=" + TS)
        self.assert_ok(res)


class TestApprove(Base):
    def test_positive_write(self):
        before = self.n_tl()
        res = call("approve", self.gd, "--command-hash=" + "c" * 64, "--decision=approved",
                   "--approver=wgen", "--note=L3 高危命令", "--timestamp=" + TS)
        self.assert_ok(res)
        ap = self.rows("approvals.tsv")
        self.assertEqual(ap[-1][0], "AP-g1-0002")
        self.assertEqual(len(ap[-1]), len(T["approvals.tsv"]))
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_verify_signoff_pass(self):
        snap = self.snap()
        res = call("approve", self.gd, "--verify-signoff=1")
        self.assertEqual(res[0], 0)
        self.assertTrue(res[1].startswith("PASS"), res[1])
        self.assertTrue(unchanged(self.gd, snap)[0])

    def test_verify_signoff_fail(self):
        write(self.gd, "approvals.tsv", [])
        snap = self.snap()
        res = call("approve", self.gd, "--verify-signoff=1")
        self.assertEqual(res[0], 1)
        self.assertTrue(res[1].startswith("FAIL"), res[1])
        self.assertTrue(unchanged(self.gd, snap)[0])

    def test_knowledge_mode(self):
        res = call("approve", self.gd, "--knowledge=1")
        self.assertEqual(res[0], 1)
        self.assert_ok(call("approve", self.gd, "--command-hash=" + "d" * 64,
                            "--decision=knowledge-approved", "--approver=wgen", "--timestamp=" + TS))
        res = call("approve", self.gd, "--knowledge=1")
        self.assertEqual(res[0], 0)

    def test_reject_bad_decision_hash_approver(self):
        snap = self.snap()
        self.assert_rej(call("approve", self.gd, "--command-hash=" + "c" * 64, "--decision=maybe",
                             "--approver=wgen", "--timestamp=" + TS), snap)
        self.assert_rej(call("approve", self.gd, "--command-hash=xyz", "--decision=approved",
                             "--approver=wgen", "--timestamp=" + TS), snapshot(self.gd))
        self.assert_rej(call("approve", self.gd, "--command-hash=" + "c" * 64, "--decision=approved",
                             "--approver=", "--timestamp=" + TS), snapshot(self.gd))


class TestMatrixSet(Base):
    def test_positive(self):
        before = self.n_tl()
        res = call("matrix-set", self.gd, "--attack-surface=web.api", "--vuln-class=inj.sql",
                   "--state=x", "--reason=FD-g1-0001", "--intent-id=INT-g1-0002", "--timestamp=" + TS)
        self.assert_ok(res)
        m = self.rows("matrix.tsv")
        key = [r for r in m if r[0] == "web.api" and r[1] == "inj.sql"]
        self.assertEqual(key[-1][T["matrix.tsv"].index("state")], "x")
        self.assertEqual(len(m), 4)
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_reject_unknown_key(self):
        snap = self.snap()
        self.assert_rej(call("matrix-set", self.gd, "--attack-surface=web.new", "--vuln-class=inj.sql",
                             "--state=x", "--timestamp=" + TS), snap, "行键")

    def test_reject_state_and_reason_rules(self):
        snap = self.snap()
        self.assert_rej(call("matrix-set", self.gd, "--attack-surface=web.api", "--vuln-class=inj.sql",
                             "--state=ok", "--timestamp=" + TS), snap)
        self.assert_rej(call("matrix-set", self.gd, "--attack-surface=web.api", "--vuln-class=inj.sql",
                             "--state=-", "--timestamp=" + TS), snapshot(self.gd), "reason")
        self.assert_rej(call("matrix-set", self.gd, "--attack-surface=web.api", "--vuln-class=inj.sql",
                             "--state=x", "--reason=submatrix:新资产", "--timestamp=" + TS),
                        snapshot(self.gd), "前缀")
        self.assert_rej(call("matrix-set", self.gd, "--attack-surface=web.api", "--vuln-class=inj.sql",
                             "--state=x", "--intent-id=INT-g1-0099", "--timestamp=" + TS), snapshot(self.gd))


class TestCheckpoint(Base):
    def test_positive_revisions(self):
        self.assertFalse(os.path.exists(os.path.join(self.gd, "state.md")))
        before = self.n_tl()
        res = call("checkpoint", self.gd, "--phase=P3", "--event=round-0", "--timestamp=" + TS)
        self.assert_ok(res)
        self.assertIn("revision=1", res[1])
        self.assertTrue(open(os.path.join(self.gd, "state.md"), encoding="utf-8").read().startswith("revision: 1"))
        res = call("checkpoint", self.gd, "--phase=P3", "--event=round-1", "--timestamp=" + TS)
        self.assertIn("revision=2", res[1])
        self.assertEqual(self.n_tl(), before + 2)
        self.assert_ledger_ok()

    def test_reject_bad_phase(self):
        snap = self.snap()
        self.assert_rej(call("checkpoint", self.gd, "--phase=P9", "--timestamp=" + TS), snap, "九门")


class TestAppendTimeline(Base):
    def test_positive(self):
        before = self.n_tl()
        res = call("append-timeline", self.gd, "--actor=总控", "--phase=P3",
                   "--event=round-end", "--timestamp=" + TS)
        self.assert_ok(res)
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_reject_side_effect_without_revert(self):
        snap = self.snap()
        res = call("append-timeline", self.gd, "--actor=子代理", "--phase=P3",
                   "--event=request: GET /api/orders", "--timestamp=" + TS)
        self.assert_rej(res, snap, "revert")

    def test_reject_bad_actor(self):
        snap = self.snap()
        self.assert_rej(call("append-timeline", self.gd, "--actor=llm", "--phase=P3",
                             "--event=x", "--timestamp=" + TS), snap)

    def test_irreversible_needs_approval(self):
        snap = self.snap()
        self.assert_rej(call("append-timeline", self.gd, "--actor=总控", "--phase=P3",
                             "--event=write-file /tmp/x", "--revert-cmd=irreversible",
                             "--timestamp=" + TS), snap, "approval")
        self.assert_ok(call("append-timeline", self.gd, "--actor=总控", "--phase=P3",
                            "--event=write-file /tmp/x", "--revert-cmd=irreversible",
                            "--approval=AP-g1-0001", "--timestamp=" + TS))


class TestMatrixFreeze(Base):
    def clear_frozen(self):
        rows = self.rows("matrix.tsv")
        fi = T["matrix.tsv"].index("frozen_at")
        for r in rows:
            r[fi] = ""
        write(self.gd, "matrix.tsv", rows)

    def test_positive(self):
        self.clear_frozen()
        before = self.n_tl()
        res = call("matrix-freeze", self.gd, "--timestamp=" + TS)
        self.assert_ok(res)
        m = self.rows("matrix.tsv")
        self.assertTrue(all(r[T["matrix.tsv"].index("frozen_at")] == TS for r in m))
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_reject_already_frozen(self):
        snap = self.snap()
        self.assert_rej(call("matrix-freeze", self.gd, "--timestamp=" + TS), snap, "重复冻结")

    def test_reject_uninitialized(self):
        write(self.gd, "matrix.tsv", [])
        snap = self.snap()
        self.assert_rej(call("matrix-freeze", self.gd, "--timestamp=" + TS), snap, "初始化")


class TestBudgetLog(Base):
    def test_positive_goal_scope(self):
        before = self.n_tl()
        res = call("budget-log", self.gd, "--token-delta=1000", "--requests-delta=25",
                   "--hours-delta=0.2", "--scope=goal", "--note=P3 轮", "--timestamp=" + TS)
        self.assert_ok(res)
        b = self.rows("budget.tsv")
        self.assertEqual(len(b[-1]), len(T["budget.tsv"]))
        self.assertEqual(b[-1][T["budget.tsv"].index("schema_version")], "2")
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_positive_intent_scope(self):
        self.assert_ok(call("budget-log", self.gd, "--token-delta=10", "--requests-delta=1",
                            "--hours-delta=0", "--scope=INT-g1-0002", "--timestamp=" + TS))

    def test_reject_dollars_when_off(self):
        snap = self.snap()
        res = call("budget-log", self.gd, "--token-delta=1", "--requests-delta=1", "--hours-delta=0",
                   "--dollars-delta=3.5", "--scope=goal", "--timestamp=" + TS)
        self.assert_rej(res, snap, "dollar")

    def test_reject_scope_and_types(self):
        snap = self.snap()
        self.assert_rej(call("budget-log", self.gd, "--token-delta=1", "--requests-delta=1",
                             "--hours-delta=0", "--scope=INT-g1-0099", "--timestamp=" + TS), snapshot(self.gd))
        self.assert_rej(call("budget-log", self.gd, "--token-delta=ten", "--requests-delta=1",
                             "--hours-delta=0", "--scope=goal", "--timestamp=" + TS), snapshot(self.gd))
        self.assert_rej(call("budget-log", self.gd, "--token-delta=1", "--requests-delta=1",
                             "--hours-delta=0", "--scope=tenant", "--timestamp=" + TS), snapshot(self.gd))
        self.assertTrue(unchanged(self.gd, snap)[0])


class TestAddCred(Base):
    BASE = ["--kind=static-cred", "--role=operator", "--username-ref=op1",
            "--secret-ref={{vault:cred-2}}", "--valid-from=2026-09-01",
            "--valid-until=2026-09-30", "--timestamp=" + TS]

    def test_positive(self):
        before = self.n_tl()
        res = call("add-cred", self.gd, *self.BASE)
        self.assert_ok(res)
        c = self.rows("creds.tsv")
        self.assertEqual(c[-1][0], "CRED-g1-0002")
        self.assertEqual(len(c[-1]), len(T["creds.tsv"]))
        self.assertEqual(c[-1][T["creds.tsv"].index("status")], "active")
        self.assertEqual(c[-1][T["creds.tsv"].index("material")], "")
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_reject_bad_placeholder_n(self):
        snap = self.snap()
        args = [a for a in self.BASE if not a.startswith("--secret-ref=")] + ["--secret-ref={{vault:cred-3}}"]
        self.assert_rej(call("add-cred", self.gd, *args), snap, "vault")
        args = [a for a in self.BASE if not a.startswith("--secret-ref=")] + ["--secret-ref=P@ssw0rd!"]
        self.assert_rej(call("add-cred", self.gd, *args), snapshot(self.gd), "真值")

    def test_reject_kind_material_and_session_rules(self):
        snap = self.snap()
        self.assert_rej(call("add-cred", self.gd, "--kind=ntlm-hash", "--role=x", "--username-ref=u",
                             "--secret-ref={{vault:cred-2}}", "--timestamp=" + TS), snap, "kind")
        sess = ["--kind=session", "--role=user", "--username-ref=u", "--secret-ref={{vault:cred-2}}"]
        self.assert_rej(call("add-cred", self.gd, *(sess + ["--timestamp=" + TS])), snapshot(self.gd), "parent_cred")
        self.assert_ok(call("add-cred", self.gd, *(sess + ["--parent-cred=CRED-g1-0001",
                                                          "--material=x509", "--timestamp=" + TS])))

    def test_reject_window_and_refs(self):
        snap = self.snap()
        args = [a for a in self.BASE if not a.startswith("--valid-until=")] + ["--valid-until=2026-08-01"]
        self.assert_rej(call("add-cred", self.gd, *args), snapshot(self.gd))
        self.assert_rej(call("add-cred", self.gd, *(list(self.BASE) + ["--obtained-via-intent=INT-g1-0099"])),
                        snapshot(self.gd))
        self.assert_rej(call("add-cred", self.gd, *(list(self.BASE) + ["--material=kerberos"])), snapshot(self.gd))
        self.assertTrue(unchanged(self.gd, snap)[0])

    def test_permitted_actions_vs_account_grant(self):
        snap = self.snap()
        self.assert_rej(call("add-cred", self.gd, *(list(self.BASE) + ["--permitted-actions=write-order"])),
                        snap, "account-grant")
        self.assert_ok(call("add-scope", self.gd, "--kind=account-grant", "--matcher=shop.example",
                            "--account=op1", "--permitted-actions=login;write-order", "--timestamp=" + TS))
        self.assert_ok(call("add-cred", self.gd, *(list(self.BASE) + ["--permitted-actions=login"])))


class TestAmendScope(Base):
    def test_positive_with_approval(self):
        before = self.n_tl()
        res = call("amend-scope", self.gd, "--amendment-of=S-g1-0001", "--kind=include",
                   "--matcher=*.shop.example", "--note=扩围至全部子域；批准人:wgen",
                   "--approval=AP-g1-0001", "--timestamp=" + TS)
        self.assert_ok(res)
        sc = self.rows("scope.tsv")
        self.assertEqual(sc[-1][0], "S-g1-0003")
        self.assertEqual(sc[-1][T["scope.tsv"].index("amendment_of")], "S-g1-0001")
        self.assertEqual(len(sc[-1]), len(T["scope.tsv"]))
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_reject_without_approval_after_p0(self):
        snap = self.snap()
        res = call("amend-scope", self.gd, "--amendment-of=S-g1-0001", "--kind=include",
                   "--matcher=*.shop.example", "--note=扩围；批准人:wgen", "--timestamp=" + TS)
        self.assert_rej(res, snap, "审批")

    def test_reject_refs_and_note(self):
        snap = self.snap()
        self.assert_rej(call("amend-scope", self.gd, "--amendment-of=S-g1-0099", "--kind=include",
                             "--matcher=*.shop.example", "--note=n",
                             "--approval=AP-g1-0001", "--timestamp=" + TS), snap)
        self.assert_rej(call("amend-scope", self.gd, "--amendment-of=S-g1-0001", "--kind=whitelist",
                             "--matcher=*.shop.example", "--note=n",
                             "--approval=AP-g1-0001", "--timestamp=" + TS), snapshot(self.gd))
        self.assert_rej(call("amend-scope", self.gd, "--amendment-of=S-g1-0001", "--kind=include",
                             "--matcher=*.shop.example", "--note=",
                             "--approval=AP-g1-0001", "--timestamp=" + TS), snapshot(self.gd))
        self.assert_rej(call("amend-scope", self.gd, "--amendment-of=S-g1-0001", "--kind=include",
                             "--matcher=*.shop.example", "--note=n",
                             "--approval=AP-g1-0099", "--timestamp=" + TS), snapshot(self.gd))


class TestSetCredStatus(Base):
    def test_query_mode(self):
        snap = self.snap()
        before = self.n_tl()
        res = call("set-cred-status", self.gd, "--id=CRED-g1-0001", "--timestamp=" + TS)
        self.assertEqual(res[0], 0)
        self.assertIn("CRED-g1-0001", res[1])
        self.assertIn("active", res[1])
        self.assertEqual(self.n_tl(), before)
        self.assertTrue(unchanged(self.gd, snap)[0])

    def test_positive_change(self):
        before = self.n_tl()
        res = call("set-cred-status", self.gd, "--id=CRED-g1-0001", "--status=expired",
                   "--note=会话过期", "--timestamp=" + TS)
        self.assert_ok(res)
        c = [r for r in self.rows("creds.tsv") if r[0] == "CRED-g1-0001"]
        self.assertEqual(len(c), 2)
        self.assertEqual(c[-1][T["creds.tsv"].index("status")], "expired")
        self.assertEqual(self.n_tl(), before + 1)
        self.assert_ledger_ok()

    def test_reject_bad_status_and_ref(self):
        snap = self.snap()
        self.assert_rej(call("set-cred-status", self.gd, "--id=CRED-g1-0001", "--status=lost",
                             "--timestamp=" + TS), snap)
        self.assert_rej(call("set-cred-status", self.gd, "--id=CRED-g1-0099", "--status=revoked",
                             "--timestamp=" + TS), snapshot(self.gd))

    def test_revival_needs_approval(self):
        self.assert_ok(call("set-cred-status", self.gd, "--id=CRED-g1-0001", "--status=revoked",
                            "--note=泄露", "--timestamp=" + TS))
        snap = self.snap()
        self.assert_rej(call("set-cred-status", self.gd, "--id=CRED-g1-0001", "--status=active",
                             "--timestamp=" + TS), snap, "approval")
        self.assert_ok(call("set-cred-status", self.gd, "--id=CRED-g1-0001", "--status=active",
                            "--approval=AP-g1-0001", "--timestamp=" + TS))


class TestErrataV2(unittest.TestCase):
    """v2 勘误护栏：findings.vuln_ref 列（dedup_key 之后）+ intents.kind+nday-verify。"""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def test_schema_dynamic_and_vuln_ref_present(self):
        f = T["findings.tsv"]
        self.assertIn("vuln_ref", f)
        self.assertEqual(f.index("vuln_ref"), f.index("dedup_key") + 1)
        self.assertEqual(sum(len(v) for v in T.values()), 147)
        self.assertIn("nday-verify", {"recon", "surface", "matrix-test", "deep-dive",
                                      "authz-diff", "nday-verify"})

    def test_add_finding_writes_vuln_ref_dynamically(self):
        before = len(read(self.gd, "findings.tsv"))
        res = call("add-finding", self.gd, "--intent-id=INT-g1-0002", "--title=Nday 组件漏洞",
                   "--confidence=C1", "--impact=中", "--exploitation-status=verified",
                   "--scope-check=in_scope", "--description-brief=Nginx 已知漏洞",
                   "--reproducible-steps=curl -s https://shop.example", "--affected-asset-id=AST-g1-0002",
                   "--evidence-ids=EV-g1-0001", "--vuln-ref=CVE-2024-1234;CWE-89", "--timestamp=" + TS)
        self.assertEqual(res[0], 0, res[1] + res[2])
        fd = read(self.gd, "findings.tsv")
        self.assertEqual(len(fd), before + 1)
        self.assertEqual(len(fd[-1]), len(T["findings.tsv"]))
        self.assertEqual(fd[-1][T["findings.tsv"].index("vuln_ref")], "CVE-2024-1234;CWE-89")

    def test_add_intent_nday_verify_kind_accepted(self):
        before = len(read(self.gd, "intents.tsv"))
        res = call("add-intent", self.gd, "--title=Nday 核验", "--engine=nday",
                   "--kind=nday-verify", "--origin=precedent", "--budget-share=100;10;1",
                   "--timestamp=" + TS)
        self.assertEqual(res[0], 0, res[1] + res[2])
        it = read(self.gd, "intents.tsv")
        self.assertEqual(len(it), before + 1)
        self.assertEqual(it[-1][T["intents.tsv"].index("kind")], "nday-verify")
        self.assertEqual(core.Session(self.gd).validate(), [])


class TestTier0AndWiring(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)

    def test_tier0_rejects_other_writes(self):
        gd = os.path.join(self.td.name, "G-g3")
        os.makedirs(gd)
        snap = snapshot(gd)
        code, out, err = call("add-scope", gd, "--kind=include", "--matcher=a.example", "--timestamp=" + TS)
        self.assertEqual(code, 1)
        self.assertIn("Tier0", err)
        self.assertTrue(unchanged(gd, snap)[0])
        code, out, err = call("add-fact", gd, "--intent-id=INT-x-0001", "--kind=info",
                              "--target=a.example", "--detail=x", "--confidence=0.5",
                              "--timestamp=" + TS)
        self.assertEqual(code, 1)

    def test_handlers_cover_19_commands_with_aliases(self):
        names = {n for n in write_cmds.HANDLERS if not n.startswith("ledger-")}
        expected = {"add-goal", "add-scope", "add-intent", "set-intent-status", "add-fact",
                    "add-finding", "supersede-finding", "add-asset", "add-edge", "add-evidence",
                    "approve", "matrix-set", "checkpoint", "append-timeline", "matrix-freeze",
                    "budget-log", "add-cred", "amend-scope", "set-cred-status"}
        self.assertEqual(names, expected)
        for n in expected:
            self.assertIn("ledger-" + n, write_cmds.HANDLERS)

    def test_registry_dispatch(self):
        from ledger import registry
        self.assertIsNotNone(registry.lookup("add-goal"))
        self.assertIsNotNone(registry.lookup("ledger-matrix-freeze"))
        self.assertIsNone(registry.lookup("no-such-cmd"))

    def test_cli_entry_paths(self):
        gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
        r = subprocess.run([sys.executable, CLI, "add-fact", "--goal-dir", gd,
                            "--intent-id=INT-g1-0001", "--kind=info", "--target=x.example",
                            "--detail=ok", "--confidence=0.5", "--timestamp=" + TS],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = subprocess.run([sys.executable, CLI, "no-such", "--goal-dir", gd],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        r = subprocess.run([sys.executable, CLI, "add-fact", "--goal-dir", gd,
                            "--intent-id=INT-g1-0001", "--kind=info", "--target=x.example",
                            "--detail=password=TopSecret123", "--confidence=0.5", "--timestamp=" + TS],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)
        r = subprocess.run([sys.executable, CLI, "verify-chain", "--goal-dir", gd],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
