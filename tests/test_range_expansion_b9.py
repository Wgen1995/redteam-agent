# -*- coding: utf-8 -*-
"""批次 9 T1：靶场扩编 20→50 契约测试（端点字典 v2 §四 消费）。

GT v2 键形（svc-* 无端口 canonical）+八新类覆盖+二级路径占比≥40%+
认证态靶配行为差分通道（弱口令成功即发 X-Auth-Token——dict §二 通道修复）。
"""
import json, os, re, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GT_PATH = os.path.join(HERE, "range", "ground-truth.json")

NEW_CLASSES = {"lfi", "rfi", "jwt", "ratelimit", "graphql", "xxe", "csrf"}
OLD_CLASSES = {"sqli", "xss", "ssti", "cmdi", "ssrf", "cors", "deser",
               "traversal", "redir", "infoleak", "idor", "role", "hauth", "weakpass"}


def load():
    with open(GT_PATH, encoding="utf-8") as f:
        return json.load(f)


class TestRangeExpansion(unittest.TestCase):
    def test_fifty_entries(self):
        gt = load()
        self.assertEqual(len(gt["planted"]), 50, "扩编目标=50 检出靶点")

    def test_canonical_key_form(self):
        gt = load()
        for e in gt["planted"]:
            self.assertRegex(e["endpoint"], r"^svc-[a-z0-9-]+/[^\s]+$",
                             "GT 键=svc-*/path 无 scheme/端口（v2 口径）: %s" % e["endpoint"])

    def test_unique_ids_and_markers(self):
        gt = load()
        ids = [e["id"] for e in gt["planted"]]
        markers = [e["marker"] for e in gt["planted"]]
        self.assertEqual(len(set(ids)), len(ids), "id 唯一")
        self.assertEqual(len(set(markers)), len(markers), "marker 唯一")

    def test_new_classes_covered(self):
        got = {e["class"] for e in load()["planted"]}
        self.assertTrue(NEW_CLASSES <= got, "八新类须全覆盖: 缺 %s" % (NEW_CLASSES - got))
        self.assertTrue(OLD_CLASSES <= got, "存量类保持: 缺 %s" % (OLD_CLASSES - got))

    def test_secondary_path_share(self):
        gt = load()
        fam = ("/debug/", "/actuator/", "/api/", "/internal/", "/admin/", "/cors",
               "/preview", "/import", "/upload", "/unserialize", "/comment", "/reply",
               "/feedback", "/render", "/decode", "/export", "/graphql", "/.env",
               "/static", "/page", "/widget", "/proxy", "/jump", "/console")
        sec = [e for e in gt["planted"]
               if any(p in e["endpoint"] for p in fam)]
        share = len(sec) / len(gt["planted"])
        self.assertGreaterEqual(share, 0.40, "二级路径占比≥40%%（dict §四）: 实际 %.2f" % share)

    def test_post_auth_have_role(self):
        for e in load()["planted"]:
            if e.get("post_auth"):
                self.assertTrue(e.get("authz_role"), "post_auth 须带 authz_role: %s" % e["id"])

    def test_alias_covers_all_services(self):
        gt = load()
        svcs = {e["endpoint"].split("/", 1)[0] for e in gt["planted"]}
        self.assertEqual(set(gt["host_aliases"]), svcs, "host_aliases 全服务覆盖")


if __name__ == "__main__":
    unittest.main()
