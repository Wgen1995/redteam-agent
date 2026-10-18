"""M1 尺子修正钉测: gt_eval 活集=同 FD-ID 末值行胜(b40 尸检: 31 假 FP 中 30=僵尸行)."""
import json, os, tempfile, unittest
from evals.gt.gt_eval import eval_session
from cli.ledger.schemas import TABLES

COLS = TABLES["findings.tsv"]

def _fd(fid, status):
    row = [""] * len(COLS)
    row[COLS.index("id")] = fid
    row[COLS.index("status")] = status
    return row

def _mk_session(rows):
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "findings.tsv"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write("\t".join(r) + "\n")
    return d

def _gt():
    p = os.path.join(tempfile.mkdtemp(), "gt.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"planted": [], "dedup": []}, f)
    return p

class TestActiveSetLastValue(unittest.TestCase):
    def _run(self, rows):
        return eval_session(_mk_session(rows), _gt())

    def test_zombie_same_id_rejected_last_wins(self):
        r = self._run([_fd("FD-1", "active"), _fd("FD-1", "rejected")])
        self.assertEqual(r["active_findings"], 0)
        self.assertEqual(r["fp"], 0)

    def test_duplicate_active_rows_count_once(self):
        r = self._run([_fd("FD-1", "active"), _fd("FD-1", "active")])
        self.assertEqual(r["active_findings"], 1)

    def test_distinct_ids_both_active(self):
        r = self._run([_fd("FD-1", "active"), _fd("FD-2", "")])
        self.assertEqual(r["active_findings"], 2)

if __name__ == "__main__":
    unittest.main()
