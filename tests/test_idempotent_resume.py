# -*- coding: utf-8 -*-
"""批次 3 T8：工件即缓存——intent done 且 submission.json 存在→重入跳过。"""
import io, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import core, phases_engine as pe

FIX = os.path.join(HERE, "fixtures", "G-g1")
TAB = chr(9)


class TestCached(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def cached(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pe.dispatch("cached", self.gd, list(args))
        return code, buf.getvalue()

    def test_done_without_file_runs(self):
        code, out = self.cached()
        self.assertEqual(code, 0)
        self.assertIn("#count=1", out)          # 夹具 INT-g1-0001=done
        self.assertIn("INT-g1-0001" + TAB + "RUN", out)   # 无 submission.json → RUN

    def test_done_with_file_skips(self):
        d = os.path.join(self.gd, "submissions", "INT-g1-0001")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "submission.json"), "w", encoding="utf-8").write("{}")
        code, out = self.cached()
        self.assertEqual(code, 0)
        self.assertIn("INT-g1-0001" + TAB + "SKIP", out)

    def test_single_intent_query(self):
        code, out = self.cached("--intent-id=INT-g1-0001")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "RUN")
        code, out = self.cached("--intent-id=INT-g1-0002")   # pending intent
        self.assertEqual(code, 0)
        self.assertIn("RUN", out)

    def test_readonly_no_side_effects(self):
        import hashlib
        before = hashlib.sha256(
            open(os.path.join(self.gd, "timeline.tsv"), "rb").read()).hexdigest()
        self.cached()
        after = hashlib.sha256(
            open(os.path.join(self.gd, "timeline.tsv"), "rb").read()).hexdigest()
        self.assertEqual(before, after)   # 查询面零副作用（§5.3 查询纪律）


if __name__ == "__main__":
    unittest.main()
