# -*- coding: utf-8 -*-
"""批次 8 T7（M10）：真人复核身份锚——approver 任意非空串放行=零身份锚反例。
名录=运行时 approvers.tsv（approvers add 登记）；approve 校验名录成员。
"""
import os, subprocess, sys, tempfile, unittest, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")
SEED = os.path.join(ROOT, "knowledge")
TS = "2026-09-27T12:00:00Z"
TAB = "\t"


def _kn(kdir, *args):
    return subprocess.run([sys.executable, KN, args[0], "--knowledge-dir", kdir] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def _fresh_kd(td):
    kd = os.path.join(td, "kn")
    shutil.copytree(SEED, kd)
    os.remove(os.path.join(kd, "approvers.example.tsv"))
    return kd


def _stage_page(kd, page="STG-0001"):
    sp = os.path.join(kd, "staging")
    os.makedirs(sp, exist_ok=True)
    with open(os.path.join(sp, "staging.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("id\tpage\tsource\tstatus\n")
    # 直接落一行 lint-passed（审批面测试聚焦身份锚，不走完整 lint 链）


class TestApproverAnchor(unittest.TestCase):
    def test_unregistered_approver_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kd = _fresh_kd(td)
            self.assertEqual(_kn(kd, "approvers", "add", "--approver=评审人甲",
                                 "--timestamp=" + TS).returncode, 0)
            # 名录外 approver 须拒（红现状：任意非空串放行）
            r = _kn(kd, "approve", "--page=STG-0001", "--approver=冒名者",
                    "--timestamp=" + TS)
            self.assertNotEqual(r.returncode, 0, "名录外 approver 必须拒收")

    def test_approvers_add_list_and_dupe(self):
        with tempfile.TemporaryDirectory() as td:
            kd = _fresh_kd(td)
            self.assertEqual(_kn(kd, "approvers", "add", "--approver=评审人甲",
                                 "--timestamp=" + TS).returncode, 0)
            self.assertEqual(_kn(kd, "approvers", "add", "--approver=评审人甲",
                                 "--timestamp=" + TS).returncode, 1, "重复登记须拒")
            r = _kn(kd, "approvers", "list")
            self.assertEqual(r.returncode, 0)
            self.assertIn("评审人甲", r.stdout)


if __name__ == "__main__":
    unittest.main()
