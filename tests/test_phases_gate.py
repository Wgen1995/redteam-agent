# -*- coding: utf-8 -*-
"""批次 3 T3：gate 断言执行器——断言→命令调用协议（phases/PROTOCOL.md §1）。
追加件（完备性设计 2bd6052 衍生）：分母就绪门 denominator-ready——matrix freeze 前置
三断言（多源法定/类覆盖/外推闭包），只读账本（facts/assets/edges/intents）。"""
import io, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import core, phases_engine as pe

FIX = os.path.join(HERE, "fixtures", "G-g1")
TAB = chr(9)
TS = "2026-09-24T08:00:00Z"


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def tl_events(self):
        ev = core.TABLES["timeline.tsv"].index("event")
        return [r[ev] for r in core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8)]

    def keep(self, pred):
        """删除满足 pred 的事件行、抹平全部 phase 门标并重算链——夹具 timeline 的 phase 列
        本身带 P0-P3（见 fixtures/G-g1/timeline.tsv 第 3 列），不抹会把 reached 抬到 P3，
        verify-chain 跳门检测随即要求 P1/P2 的 gate-exit 在场（test_query_check.py:545 同源语义）。"""
        p = os.path.join(self.gd, "timeline.tsv")
        ph = core.TABLES["timeline.tsv"].index("phase")
        rows = [r for r in core.read_tsv(p, 8) if not pred(r[3])]
        prev = core.GENESIS
        for r in rows:
            r[ph] = ""
            r[5] = prev
            r[6] = core.row_hash(prev, [r[j] for j in (0, 1, 2, 3, 4, 5, 7)])
            prev = r[6]
        core.write_tsv(p, rows)

    def add_scope_row(self, kind, matcher):
        from ledger import write_cmds
        write_cmds.HANDLERS["add-scope"](self.gd, [
            "--kind=" + kind, "--matcher=" + matcher, "--note=b3test",
            "--timestamp=" + TS])

    def call(self, *args):
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            code = pe.dispatch("gate", self.gd, list(args))
        return code, buf_o.getvalue(), buf_e.getvalue()


class TestGate(Base):
    def test_already_passed_idempotent(self):
        before = sum(1 for e in self.tl_events() if e.startswith("gate-exit:P0"))
        code, out, _ = self.call("--phase=P0", "--timestamp=" + TS)
        self.assertEqual(code, 0)
        self.assertIn("already-passed", out)
        after = sum(1 for e in self.tl_events() if e.startswith("gate-exit:P0"))
        self.assertEqual(before, after)   # 不重复落事件

    def test_gate_p0_runs_assertions_for_real(self):
        self.keep(lambda ev: ev.startswith("gate-exit:"))   # 抹掉全部过门事件+门标
        # 夹具 scope.tsv 只有 include 两行——P0 断言 ledger-scope-coverage 要求
        # include+exclude+oob 齐备，先经正规写命令补两行（顺带验链式延续）
        self.add_scope_row("exclude", "db.shop.example")
        self.add_scope_row("oob", "callbacks.example")
        code, out, err = self.call("--phase=P0", "--timestamp=" + TS)
        self.assertEqual(code, 0, out + err)
        evs = self.tl_events()
        self.assertTrue(any(e.startswith("gate-exit:P0 asserts=3 result=PASS") for e in evs))
        r = __import__("subprocess").run(
            [sys.executable, os.path.join(ROOT, "cli", "tanyin-ledger"),
             "verify-chain", "--goal-dir", self.gd], capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout)   # 新事件链一致且跳门检测通过

    def test_gate_fail_records_gate_fail_not_exit(self):
        self.keep(lambda ev: ev.startswith("gate-exit:"))
        # 破坏 P0 断言前提：删掉 oob scope 行（ledger-scope-coverage 会 FAIL）
        p = os.path.join(self.gd, "scope.tsv")
        rows = [r for r in core.read_tsv(p, 9) if r[1] != "oob"]
        core.write_tsv(p, rows)
        code, out, err = self.call("--phase=P0", "--timestamp=" + TS)
        self.assertEqual(code, 1)
        self.assertTrue(any(e.startswith("gate-fail:P0") for e in self.tl_events()))
        self.assertFalse(any(e.startswith("gate-exit:P0") for e in self.tl_events()))

    def test_predecessor_required(self):
        self.keep(lambda ev: ev.startswith("gate-exit:"))
        before = len(self.tl_events())
        code, out, _ = self.call("--phase=P2", "--timestamp=" + TS)   # P0/P1 未过
        self.assertEqual(code, 1)
        self.assertIn("前置门未过", out)
        # 零落账＝REJECT 不新增任何事件（Ruling：计划原文断言 len==0 与其 keep() 语义
        # 自相矛盾——夹具尚有 4 条非门事件；按注释意图「零落账」改为前后计数不变）
        self.assertEqual(len(self.tl_events()), before)

    def test_p3_converge_degraded_mode(self):
        # 夹具已过 P0-P3；构造 budget-exhausted：goal requests 限额压到已用之下
        gi = core.TABLES["goals.tsv"].index("budget")
        p = os.path.join(self.gd, "goals.tsv")
        rows = core.read_tsv(p, 19)
        rows[0][gi] = "1;10;40"
        core.write_tsv(p, rows)
        self.keep(lambda ev: ev.startswith("gate-exit:P3"))
        code, out, err = self.call("--phase=P3", "--timestamp=" + TS)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(any(e.startswith("gate-exit:P3 asserts=1 result=PASS mode=degraded")
                            for e in self.tl_events()))


# ---------------------------------------------------------------------------
# 追加件（完备性设计 2bd6052 §1.3 衍生，获批随 T3 落）：分母就绪门。
# 三断言：①多源法定（每 in_scope 资产来源数>=2 或 unverified+在队列继续挖任务）
# ②A1-A8 类覆盖（类非空或不适用理由落账）③外推闭包（无未处理悬空外推节点）。
# 读侧约定（PROTOCOL.md §4 冻结）：来源=指向该资产值的 fact 之 distinct intent_id 数；
# unverified 标记=assets.meta 含 "unverified"；不适用理由=fact(kind=info,
# target=asset-class:A<k>)；外推标记=assets.meta 含 "extrapolated"/"外推"；
# 在队列继续挖=intents(status=pending, kind=recon, dedup_key 以 "<AST-id>+" 开头
# 或 title/detail 含资产值)；已处理=有采集 fact/绑定 intent(任意状态)/整合边
# (kind in parent/attack/scope-rel 触及其 id)。界外资产不入①（触发器目录：记录不测）。
class DenomBase(Base):
    def dr(self, *args):
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            code = pe.dispatch("denominator-ready", self.gd, list(args))
        return code, buf_o.getvalue(), buf_e.getvalue()

    def fail_lines(self, out):
        return [l.strip() for l in out.splitlines() if l.startswith("  ")]

    def set_meta(self, asset_id, meta):
        p = os.path.join(self.gd, "assets.tsv")
        rows = core.read_tsv(p, 7)
        for r in rows:
            if r[0] == asset_id:
                r[core.TABLES["assets.tsv"].index("meta")] = meta
        core.write_tsv(p, rows)

    def add_intent(self, title, asset="", kind="recon", origin="recon-event"):
        from ledger import write_cmds
        args = ["--title=" + title, "--engine=web-blackbox", "--kind=" + kind,
                "--origin=" + origin, "--budget-share=1;1;1", "--timestamp=" + TS]
        if asset:
            args.append("--asset=" + asset)
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            rc = write_cmds.HANDLERS["add-intent"](self.gd, args)
        assert rc == 0, buf.getvalue()

    def add_fact(self, target, detail="补第二来源", intent="INT-g1-0001", kind="info"):
        from ledger import write_cmds
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            rc = write_cmds.HANDLERS["add-fact"](self.gd, [
                "--intent-id=" + intent, "--kind=" + kind, "--target=" + target,
                "--detail=" + detail, "--confidence=0.9", "--timestamp=" + TS])
        assert rc == 0, buf.getvalue()

    def add_asset(self, value, meta="", atype="subdomain"):
        from ledger import write_cmds
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            rc = write_cmds.HANDLERS["add-asset"](self.gd, [
                "--type=" + atype, "--value=" + value, "--meta=" + meta,
                "--timestamp=" + TS])
        assert rc == 0, buf.getvalue()

    def snap_tables(self):
        out = {}
        for t in core.TABLES:
            p = os.path.join(self.gd, t)
            if os.path.exists(p):
                with open(p, "rb") as f:
                    out[t] = f.read()
            else:
                out[t] = None
        return out


class TestDenominatorReady(DenomBase):
    def test_fixture_fail_list_shape(self):
        """G-g1 基线＝FAIL 清单：①两条 in_scope 单源（界外 vpn 豁免）②A2-A8 七类空。"""
        code, out, err = self.dr()
        self.assertEqual(code, 1, out + err)
        self.assertIn("FAIL" + TAB + "denominator-ready", out)
        src = [l for l in self.fail_lines(out) if l.startswith("①")]
        cls = [l for l in self.fail_lines(out) if l.startswith("②")]
        self.assertEqual(len(src), 2)
        self.assertIn("AST-g1-0001", src[0]); self.assertIn("AST-g1-0002", src[1])
        self.assertTrue(all("AST-g1-0003" not in l for l in src))   # 界外不入①
        self.assertEqual(len(cls), 7)                                # A1 非空（root-domain+subdomain）
        for k in range(2, 9):
            self.assertTrue(any("A%d" % k in l for l in cls), "缺 A%d 行" % k)
        self.assertFalse([l for l in self.fail_lines(out) if l.startswith("③")])
        self.assertIn("9", out.splitlines()[0])   # 2+7=9 项

    def test_readonly_zero_side_effects(self):
        before = self.snap_tables()
        code, out, _ = self.dr()
        self.assertEqual(code, 1)
        self.assertEqual(self.snap_tables(), before)   # 只读账本，13 表字节不变

    def test_second_intent_source_clears_check1(self):
        """来源数=distinct intent_id：换一个新 intent 补一条 fact 即达 2 源。"""
        self.add_intent("证书透明度补源")
        self.add_fact("shop.example", intent="INT-g1-0003")
        self.add_fact("admin-internal.shop.example", intent="INT-g1-0003")
        code, out, _ = self.dr()
        self.assertEqual(code, 1)
        self.assertFalse([l for l in self.fail_lines(out) if l.startswith("①")])
        self.assertEqual(len([l for l in self.fail_lines(out) if l.startswith("②")]), 7)

    def test_unverified_plus_queued_dig_escape(self):
        """豁免通道：meta 标 unverified 且有绑定该资产的在队列 recon intent。"""
        self.set_meta("AST-g1-0001", "unverified")
        self.set_meta("AST-g1-0002", "unverified")
        code, out, _ = self.dr()   # 仅标 unverified、无在队列任务 → ①仍在
        src = [l for l in self.fail_lines(out) if l.startswith("①")]
        self.assertEqual(len(src), 2)
        self.assertTrue(all("在队列继续挖=否" in l for l in src))
        self.add_intent("继续挖 shop.example", asset="AST-g1-0001")
        self.add_intent("继续挖 admin-internal.shop.example", asset="AST-g1-0002")
        code, out, _ = self.dr()
        self.assertFalse([l for l in self.fail_lines(out) if l.startswith("①")])

    def test_class_na_reason_or_asset_fills_check2(self):
        """不适用理由落账（fact target=asset-class:A<k>）或该类资产存在。"""
        for k in range(2, 9):
            self.add_fact("asset-class:A%d" % k, detail="不适用：批注理由", kind="info")
        self.add_intent("补源B")
        self.add_fact("shop.example", intent="INT-g1-0003")
        self.add_fact("admin-internal.shop.example", intent="INT-g1-0003")
        code, out, err = self.dr()
        self.assertEqual(code, 0, out + err)
        self.assertIn("PASS" + TAB + "denominator-ready", out)

    def test_dangling_extrapolation_node_check3(self):
        """外推资产（meta=extrapolated）无 fact/绑定 intent/整合边=悬空；补任一即闭环。"""
        self.add_asset("evil.example", meta="extrapolated:same-cert")   # 界外（不匹配 include）
        code, out, _ = self.dr()
        dang = [l for l in self.fail_lines(out) if l.startswith("③")]
        self.assertEqual(len(dang), 1)
        self.assertIn("evil.example", dang[0])
        self.add_fact("evil.example", detail="外推处置：同证书关联域登记")   # 采集 fact=已处理
        code, out, _ = self.dr()
        self.assertFalse([l for l in self.fail_lines(out) if l.startswith("③")])
        # 整合边亦闭环：新外推节点经 parent 边接入图谱主体
        self.add_asset("cdn.example", meta="外推:同 analytics id")
        code, out, _ = self.dr()
        self.assertEqual(len([l for l in self.fail_lines(out) if l.startswith("③")]), 1)
        from ledger import write_cmds
        arows = core.read_tsv(os.path.join(self.gd, "assets.tsv"), 7)
        cdn = next(r[0] for r in arows if r[2] == "cdn.example")
        root = next(r[0] for r in arows if r[2] == "shop.example")
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            rc = write_cmds.HANDLERS["add-edge"](self.gd, [
                "--kind=parent", "--source-id=" + root, "--target-id=" + cdn,
                "--provenance=P3", "--timestamp=" + TS])
        assert rc == 0, buf.getvalue()
        code, out, _ = self.dr()
        self.assertFalse([l for l in self.fail_lines(out) if l.startswith("③")])

    def test_usage_error_exit_2(self):
        code, out, err = self.dr("--bogus=1")
        self.assertEqual(code, 2)

    def test_cli_surface_and_golden_lock(self):
        """CLI 面（[sys.executable, 入口]）+ fixture 基线金样锁定+双跑确定性。"""
        import subprocess
        cli = os.path.join(ROOT, "cli", "tanyin-phases")
        r = subprocess.run([sys.executable, cli, "denominator-ready",
                            "--goal-dir", self.gd], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("FAIL", r.stdout)
        # 双跑字节一致（确定性投影）
        gd2 = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1b"))
        r2 = subprocess.run([sys.executable, cli, "denominator-ready",
                             "--goal-dir", gd2], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
        self.assertEqual(r.stdout, r2.stdout)
        # 金样基线（tests/golden/phases-denominator-ready.norm，随本任务建档）
        gp = os.path.join(HERE, "golden", "phases-denominator-ready.norm")
        self.assertTrue(os.path.isfile(gp), "金样缺失: " + gp)
        with open(gp, encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), r.stdout.strip())


if __name__ == "__main__":
    unittest.main()
