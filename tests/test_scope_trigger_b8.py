# -*- coding: utf-8 -*-
"""批次 8 T3+T4：scope_asset 悬空写侧拒收+图读侧告警（M5）/触发器第九类机检（M6）。
红=复现形式化专家反例：--scope-asset=AST-g1-9999 exit 0+图静默丢边+端口服务变更零机检。
"""
import io, os, sys, unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
sys.path.insert(0, os.path.join(HERE, ".."))
from tests.test_write_cmds import Base, call, write, T, TS
from ledger import graph_cmds, phases_engine


class TestScopeAssetDangling(Base):
    def test_write_reject_dangling(self):
        snap = self.snap()
        self.assert_rej(call("add-cred", self.gd, "--kind=session", "--role=user",
                             "--username-ref=vault:u1", "--secret-ref={{" + "vault:cred-2}}",
                             "--parent-cred=CRED-g1-0001",
                             "--scope-asset=AST-g1-9999", "--timestamp=" + TS), snap, "悬空")

    def test_graph_warns_dangling(self):
        # 夹具铸一条悬空（绕过写侧：直写 TSV 模拟历史遗留），图命令须 stderr 告警
        rows = self.rows("creds.tsv")
        bad = list(rows[-1]); bad[T["creds.tsv"].index("id")] = "CRED-g1-9999"
        bad[T["creds.tsv"].index("scope_asset")] = "AST-g1-9999"
        rows.append(bad)
        write(self.gd, "creds.tsv", rows)
        buf_e = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(buf_e):
            graph_cmds.HANDLERS["graph-neighbors"](self.gd, ["--asset=CRED-g1-9999"])
        self.assertIn("悬空", buf_e.getvalue())


class TestTriggerPortChange(Base):
    def _port_fact(self, consume=False):
        ref = "（复测引用 INT-g1-0002）" if consume else ""
        self.assert_ok(call("add-fact", self.gd, "--intent-id=INT-g1-0001",
                            "--kind=port", "--confidence=0.9",
                            "--detail=端口 8080 新开放%s" % ref,
                            "--target=AST-g1-0002:8080", "--timestamp=" + TS))

    def test_unconsumed_port_change_fails_audit(self):
        self._port_fact()
        fails, st = phases_engine.trigger_audit(self.gd)
        joined = "\n".join(fails)
        self.assertIn("⑤", joined)

    def test_consumed_port_change_passes(self):
        self._port_fact()
        self.assert_ok(call("add-intent", self.gd, "--title=指纹重测 AST-g1-0002:8080",
                            "--engine=web-blackbox", "--kind=deep-dive", "--origin=entity",
                            "--budget-share=100;10;1", "--timestamp=" + TS))
        fails, _st = phases_engine.trigger_audit(self.gd)
        self.assertFalse([f for f in fails if f.startswith("⑤")])


if __name__ == "__main__":
    unittest.main()
