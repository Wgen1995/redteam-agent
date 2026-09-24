# -*- coding: utf-8 -*-
"""批次4 T9：vuln-agent 适配器——归一化表+统一提交 schema 合规+POC 四要素门。

FD 报告卡规格（2026-09-24 b0006f2 §一.6/§三）：外部发现强制 POC 四要素
（raw_request/raw_response/时间/环境），缺一=降级 fact 不成 finding。"""
import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTER = os.path.join(HERE, "..", "engines", "vuln-agent", "adapter.py")
FIXOUT = os.path.join(HERE, "fixtures", "engine", "vuln-agent-out")


class TestVulnAdapter(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()

    def adapt(self):
        return subprocess.run([sys.executable, ADAPTER, "--intent-id", "INT-g1-0099",
                               "--out-dir", self.out, "--source", FIXOUT],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def test_submission_schema_conform(self):
        r = self.adapt()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sub = json.load(open(os.path.join(self.out, "submission.json"), encoding="utf-8"))
        for f in ("intent_id", "engine", "status", "facts", "findings", "assets",
                  "edges", "creds", "operations_log"):
            self.assertIn(f, sub)
        self.assertEqual(sub["engine"], "vuln-agent")
        self.assertEqual(sub["status"], "done")
        self.assertTrue(os.path.isfile(os.path.join(self.out, "operations.log")))

    def test_three_tier_mapping(self):
        self.adapt()
        sub = json.load(open(os.path.join(self.out, "submission.json"), encoding="utf-8"))
        by_conf = {}
        for f in sub["findings"]:
            by_conf.setdefault(f["confidence"], []).append(f)
        self.assertIn("C2", by_conf, "VULN→C2")
        self.assertIn("C3", by_conf, "SUSPECTED→C3")
        vuln = by_conf["C2"][0]
        self.assertEqual(vuln["exploitation_status"], "suspected")
        self.assertEqual(vuln["network_position"], "same-host")
        self.assertEqual(vuln["impact"], "高")
        self.assertTrue(vuln["reproducible_steps"], "Payload 段进复现步骤")
        novuln = [f for f in sub["facts"] if "排除" in f["detail"]]
        self.assertTrue(novuln, "NOVULN→fact info")

    def test_review_final_prefix_wins(self):
        self.adapt()
        sub = json.load(open(os.path.join(self.out, "submission.json"), encoding="utf-8"))
        self.assertEqual(len([f for f in sub["findings"] if f["confidence"] == "C2"]), 1,
                         "复核维持=单 VULN；复核翻案（NOVULN 前缀终态）则不进 findings")

    def test_poc_four_elements_missing_downgrades_to_fact(self):
        """FD 报告卡规格 b0006f2：缺任一要素的 VULN=降级 fact（kind=vuln-clue）不成 finding。"""
        self.adapt()
        sub = json.load(open(os.path.join(self.out, "submission.json"), encoding="utf-8"))
        down = [f for f in sub["facts"] if "降级" in f["detail"]]
        self.assertTrue(down, "缺 POC 四要素的 VULN-4 须降级 fact")
        self.assertEqual(down[0]["kind"], "vuln-clue")
        for k in ("raw_request", "raw_response", "时间", "环境"):
            self.assertIn(k, down[0]["detail"], "detail 须点名缺失要素")
        self.assertEqual(down[0]["target"], "iface-rest-user-controller-4")
        locs = " ".join(f.get("location", "") for f in sub["findings"])
        self.assertNotIn("HealthController.java:18", locs, "缺四要素不进 findings")

    def test_poc_elements_carried_into_finding(self):
        """四要素随提交携带：raw_request/raw_response 原文进步骤、时间进证据引用。"""
        self.adapt()
        sub = json.load(open(os.path.join(self.out, "submission.json"), encoding="utf-8"))
        vuln = [f for f in sub["findings"] if f["confidence"] == "C2"][0]
        steps = "\n".join(vuln["reproducible_steps"])
        self.assertIn("GET /api/users?sort=id,(SELECT 1) HTTP/1.1", steps,
                      "raw_request 原文进复现步骤（Burp 直贴可重放）")
        self.assertIn("HTTP/1.1 200 OK", steps, "raw_response 原文进复现步骤")
        self.assertIn("2026-09-24T10:22:05+08:00", " ".join(vuln["evidence_refs"]),
                      "时间随证据引用（源文件@时间戳）携带")


if __name__ == "__main__":
    unittest.main()
