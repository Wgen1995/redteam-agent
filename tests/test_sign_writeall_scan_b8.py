# -*- coding: utf-8 -*-
"""批次 8 T9（G-44）：write_all 三工件门内化——先落盘后签发，
pass.json artifacts 绑定 findings.json/sarif/report-*.md；篡改即 lint 复检拒。
红现状=工件落盘居 sign_gate 之后（门内不可达，绑定零覆盖）。
"""
import hashlib, json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from tests.test_sign_gates_b7 import _fresh_gd, TS
from ledger import report_lint


class TestWriteAllInGate(unittest.TestCase):
    def test_pass_json_binds_write_all_artifacts(self):
        gd = _fresh_gd(self)
        rc = report_lint.cmd_sign(gd, TS)
        self.assertEqual(rc, 0)
        with open(os.path.join(gd, "report", "signed", "pass.json"), encoding="utf-8") as f:
            arts = json.load(f).get("artifacts")
        self.assertIn("report/findings.json", arts,
                      "红现状：findings.json 未入绑定（落盘居门后）: %s" % sorted(arts or {}))
        with open(os.path.join(gd, "report", "findings.json"), "rb") as f:
            self.assertEqual(hashlib.sha256(f.read()).hexdigest(), arts["report/findings.json"])

    def test_tampered_findings_json_rejected_by_lint(self):
        gd = _fresh_gd(self)
        self.assertEqual(report_lint.cmd_sign(gd, TS), 0)
        fj = os.path.join(gd, "report", "findings.json")
        with open(fj, "a", encoding="utf-8") as f:
            f.write("tampered\n")
        rc, rep = report_lint.sign_gate(gd, TS, write_credential=False)
        self.assertEqual(rc, 1, "绑定复检必须拒篡改 findings.json")


if __name__ == "__main__":
    unittest.main()
