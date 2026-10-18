# -*- coding: utf-8 -*-
"""功能11补件一·误报哨兵钉测（设计 docs/design/2026-10-20-sentinel-retest-design.md §补件一）。

四态钉：downgrade-to-fact（降级走 facts 不入 findings）/ reject（写前拒收零字节
变更）/ mark-suspicious（降 exploitation_status=suspected 待验证官）/ clear（全清
正常入库）——外加：规则加载版本化（version 行+加载记日志）/ 金样同输入同判 /
K6 回流（重放证伪教训→哨兵规则草稿进 staging，不自动生效）。

律：纯 stdlib、3.9 兼容、全本地夹具零外联（哨兵=确定性纯函数，零 LLM 调用）。
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)

from ledger import judge_client as jc  # noqa: E402  红点：哨兵引擎缺=AttributeError 全红
from cli.knowledge import distill as D  # noqa: E402
from tests.test_knowledge_distill import fd_row, kdir, make_battle, tl_row  # noqa: E402
from tests.test_report_lint import repair_auth  # noqa: E402  夹具修补单源

FIX = os.path.join(HERE, "fixtures", "G-g1")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
EV_ID = "EV-g1-0002"
RAW_REQUEST = "GET /admin/orders HTTP/1.1\nHost: admin-internal.shop.example\nAccept: */*"

# 全清金样（=test_report_artifacts._mint 同款语料——既有铸路不得被哨兵误伤）。
CLEAR_TITLE = "admin 面板匿名可读（哨兵全清金样）"
CLEAR_BRIEF = "未登录可读订单列表（双工件夹具）"
CLEAR_STEPS = "匿名 GET /admin/orders;响应 200 含订单列表"

# 14 条真教训样本（b40 尸检+RT 复盘误报形态，一规则一样本）。
SAMPLES = {
    "SEN-001": "未授权访问: /api/v2/orders 返回404页面即可访问",
    "SEN-002": "目标根路径为 nginx 默认页面,构成信息泄露风险",
    "SEN-003": "SQL 注入 payload 触发 WAF 拦截页面,判定存在防火墙绕过漏洞",
    "SEN-004": "时间盲注: sleep(5) 后响应延迟明显增加,判定注入存在",
    "SEN-005": "命令注入: 工具输出被截断,回显段存在命令执行痕迹",
    "SEN-006": "重复上报: 复测再次发现同款问题",
    "SEN-007": "硬编码凭据: 单元测试样例密码 test/admin 被判定真实有效",
    "SEN-008": "注入后返回状态码 500 但判定利用成功",
    "SEN-009": "未授权访问: /admin 返回302重定向到登录页,判定可绕过认证",
    "SEN-010": "敏感信息泄露: 报错页暴露完整堆栈",
    "SEN-011": "代理返回低置信判断(可能存在漏洞),未实测直接记为已验证",
    "SEN-012": "布尔盲注成立: 两次请求响应完全一致,仍判定存在注入",
    "SEN-013": "nmap 扫描超时,判定该端口服务不可达已关闭",
    "SEN-014": "弱加密: 站点部署自签证书,判定 TLS 配置漏洞",
}


def run(*args):
    return subprocess.run([sys.executable] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def _corpus(title, brief, steps):
    return title + "\n" + brief + "\n" + steps


# ================================================================ 规则加载 ==

class TestSentinelLoading(unittest.TestCase):
    def test_repo_rule_file_loads_14_versioned(self):
        self.assertTrue(os.path.isfile(jc.SENTINELS_PATH),
                        "规则文件缺席: %s" % jc.SENTINELS_PATH)
        version, rules = jc.load_sentinels()
        self.assertEqual(version, "1")
        self.assertEqual(len(rules), 14)
        ids = [r["id"] for r in rules]
        self.assertEqual(len(set(ids)), 14, "id 重复")
        self.assertEqual(ids, sorted(ids), "id 须文件序单调")
        import re
        for r in rules:
            self.assertEqual(tuple(k for k in r),
                             ("id", "signal_pattern", "judge", "action", "note"))
            re.compile(r["signal_pattern"])  # 全部可编译
            self.assertIn(r["action"], jc.SENTINEL_ACTIONS)
            self.assertTrue(r["judge"].strip() and r["note"].strip(), "判据/教训非空")
        acts = {r["action"] for r in rules}
        self.assertEqual(acts, set(jc.SENTINEL_ACTIONS), "三种处置须齐")

    def test_version_logged_on_load(self):
        with self.assertLogs("tanyin.sentinels", level="INFO") as lg:
            jc.load_sentinels()
        self.assertTrue(any("version=1" in ln for ln in lg.output),
                        "加载须记版本入日志: %r" % lg.output)

    def test_custom_path_version_and_bad_rows(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        p = os.path.join(tmp, "s.tsv")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("# version: 7\n")
            f.write("id\tsignal_pattern\tjudge\taction\tnote\n")
            f.write("SEN-X1\t(?i)abc\t判据\tmark-suspicious\tn1\n")
            f.write("SEN-X2\t(?i)b(c\t判据\tmark-suspicious\tn2\n")   # 坏 regex
            f.write("SEN-X3\t(?i)ok\t判据\tfly\tn3\n")                # 坏 action
            f.write("SEN-X4\t(?i)ok\t判据\tmark-suspicious\n")          # 坏列数
            f.write("SEN-X1\t(?i)dup\t判据\treject\tn5\n")             # 重复 id
        version, rules = jc.load_sentinels(p)
        self.assertEqual(version, "7")
        self.assertEqual([r["id"] for r in rules], ["SEN-X1"])

    def test_missing_file_fail_closed_clear(self):
        with self.assertLogs("tanyin.sentinels", level="WARNING") as lg:
            version, rules = jc.load_sentinels("/nonexistent/s.tsv")
            v = jc.run_sentinels("返回404页面即可访问 构成漏洞", path="/nonexistent/s.tsv")
        self.assertEqual((version, rules), ("", []))
        self.assertEqual(v["action"], "clear")
        self.assertTrue(any("fail-closed" in ln or "unavailable" in ln
                            for ln in lg.output))


# ================================================================ 四态+金样 ==

class TestSentinelVerdicts(unittest.TestCase):
    def test_clear_on_existing_mint_corpus(self):
        """全清金样：既有铸路语料（test_report_artifacts._mint 同款）不得被误伤。"""
        v = jc.run_sentinels(_corpus(CLEAR_TITLE, CLEAR_BRIEF, CLEAR_STEPS))
        self.assertEqual(v["action"], "clear")
        self.assertEqual(v["rule_ids"], [])
        self.assertEqual(v["note"], "")

    def test_each_rule_fires_on_its_lesson_sample(self):
        _, rules = jc.load_sentinels()
        by_id = {r["id"]: r for r in rules}
        for rid, sample in SAMPLES.items():
            with self.subTest(rule=rid):
                self.assertIn(rid, by_id, "样本指向不存在的规则")
                v = jc.run_sentinels(sample)
                self.assertIn(rid, v["rule_ids"], "样本未命中: %s" % sample)
                self.assertEqual(v["action"], by_id[rid]["action"])

    def test_gold_404_pinned_and_deterministic(self):
        """金样钉死：同输入同判（两跑逐字节一致+落点钉死）。"""
        corpus = SAMPLES["SEN-001"]
        v1 = jc.run_sentinels(corpus)
        v2 = jc.run_sentinels(corpus)
        self.assertEqual(v1, v2)
        self.assertEqual(v1["action"], "downgrade-to-fact")
        self.assertEqual(v1["rule_ids"], ["SEN-001"])
        self.assertEqual(v1["version"], "1")

    def test_precedence_reject_beats_downgrade(self):
        corpus = SAMPLES["SEN-011"] + "\n" + SAMPLES["SEN-014"]
        v = jc.run_sentinels(corpus)
        self.assertEqual(v["action"], "reject")
        self.assertIn("SEN-011", v["rule_ids"])

    def test_precedence_downgrade_beats_suspicious(self):
        corpus = SAMPLES["SEN-001"] + "\n" + SAMPLES["SEN-004"]
        v = jc.run_sentinels(corpus)
        self.assertEqual(v["action"], "downgrade-to-fact")
        self.assertIn("SEN-001", v["rule_ids"])


# ================================================================ 入库挂接 ==

class TestIngestionHook(unittest.TestCase):
    """add-finding 入库路径前置哨兵（write_cmds 最小挂接）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        repair_auth(self.gd)
        art = os.path.join(self.gd, "evidence", EV_ID + ".raw")
        os.makedirs(os.path.dirname(art), exist_ok=True)
        with open(art, "w", encoding="utf-8", newline="\n") as f:
            f.write(RAW_REQUEST)
        r = run(LEDGER, "add-evidence", "--goal-dir", self.gd,
                "--title=admin 面板匿名可读-哨兵测", "--source-type=capture",
                "--observed-at=2026-09-23T02:30:00Z", "--network-position=intranet",
                "--repro-command=curl -s http://admin-internal.shop.example/admin/orders",
                "--repro-kind=single", "--artifact=evidence/" + EV_ID + ".raw",
                "--raw-excerpt=HTTP/1.1 200 OK 订单列表脱敏样例",
                "--timestamp=2026-09-23T02:35:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def _snap(self):
        out = {}
        for nm in sorted(os.listdir(self.gd)):
            if nm.endswith(".tsv"):
                with open(os.path.join(self.gd, nm), "rb") as f:
                    out[nm] = f.read()
        return out

    def _add_finding(self, title, brief, steps, exploit="verified"):
        return run(LEDGER, "add-finding", "--goal-dir", self.gd,
                   "--intent-id=INT-g1-0002", "--title=" + title,
                   "--confidence=C1", "--impact=高",
                   "--exploitation-status=" + exploit, "--scope-check=in_scope",
                   "--description-brief=" + brief,
                   "--reproducible-steps=" + steps,
                   "--affected-asset-id=AST-g1-0002",
                   "--evidence-ids=" + EV_ID,
                   "--timestamp=2026-09-23T03:30:00Z")

    def _findings_rows(self):
        from ledger.core import Session
        return Session(self.gd).rows("findings.tsv")

    def test_downgrade_writes_fact_not_finding(self):
        from ledger.core import Session
        from ledger.schemas import TABLES
        before = self._snap()
        r = self._add_finding("未授权访问: /api/v2/orders", "接口返回404页面即可访问",
                              "GET /api/v2/orders;404 页面")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("facts.tsv", r.stdout)  # OK 行落 facts
        self.assertEqual(len(self._findings_rows()), 1, "findings 仍只有夹具 1 行")
        self.assertEqual(before["findings.tsv"], self._snap()["findings.tsv"],
                         "findings 表零字节变更")
        facts = Session(self.gd).rows("facts.tsv")
        row = facts[-1]
        ti = TABLES["facts.tsv"]
        self.assertEqual(row[ti.index("kind")], "info")
        detail = row[ti.index("detail")]
        self.assertIn("哨兵降级", detail)
        self.assertIn("SEN-001", detail)
        tl = Session(self.gd).rows("timeline.tsv")
        self.assertTrue(any(r2[3].startswith("add-fact F-") for r2 in tl),
                        "timeline 须留 add-fact 事件")

    def test_reject_refuses_zero_change(self):
        before = self._snap()
        r = self._add_finding("未验证漏洞上报", "代理返回低置信判断,未实测记为已验证",
                              "GET /x;代理返回低置信判断(可能存在漏洞),未实测记为已验证")
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)
        self.assertIn("哨兵", r.stderr)
        self.assertIn("SEN-011", r.stderr)
        self.assertEqual(before, self._snap(), "13 表零字节变更")

    def test_mark_suspicious_demotes_verified(self):
        from ledger.schemas import TABLES
        r = self._add_finding("时间盲注", "sleep(5) 后响应延迟明显增加",
                              "GET /x?id=1 AND sleep(5);延迟增加判定注入存在")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rows = self._findings_rows()
        xi = TABLES["findings.tsv"].index("exploitation_status")
        self.assertEqual(rows[-1][xi], "suspected", "verified 不可带哨兵命中入账")

    def test_clear_passes_normal(self):
        from ledger.schemas import TABLES
        r = self._add_finding(CLEAR_TITLE, CLEAR_BRIEF, CLEAR_STEPS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rows = self._findings_rows()
        xi = TABLES["findings.tsv"].index("exploitation_status")
        self.assertEqual(rows[-1][xi], "verified", "全清=正常入库")


# ================================================================ K6 回流 ==

class TestK6Backflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        with open(jc.SENTINELS_PATH, "rb") as f:
            self.rules_bytes = f.read()

    def test_fp_battle_yields_staged_draft(self):
        tl = [tl_row("2026-10-20T11:00:00Z",
                     "replay:FD-r1-0002:REJECTED note=环境差异变更")]
        bd = make_battle(self.tmp, findings=[fd_row(2, exploit="verified")],
                         timeline=tl, settle="recall=0.5 (1/2)\n")
        out = os.path.join(self.tmp, "out1")
        rep = D.distill_battle(bd, out=out, knowledge_dir=kdir(self.tmp))
        sp = os.path.join(out, "sentinel-staging", "battle-1--sentinel-drafts.tsv")
        self.assertTrue(os.path.isfile(sp), "草稿须落 staging: %s" % sp)
        with open(sp, encoding="utf-8") as f:
            text = f.read()
        self.assertTrue(text.startswith("# version: draft"), "草稿头带 version 行")
        self.assertIn("id\tsignal_pattern\tjudge\taction\tnote", text)
        self.assertIn("SEN-D-001", text)
        self.assertIn("(?i)", text.splitlines()[4])  # pattern 形
        self.assertIn("mark-suspicious", text)
        self.assertIn("FD-r1-0002", text)
        self.assertIn("重放证伪", text)
        self.assertIn("人工", text)  # 人工确认位说明
        self.assertEqual(rep["counts"]["sentinel_drafts"], 1)
        # 不自动生效：规则文件逐字节未动 + 加载面不变
        with open(jc.SENTINELS_PATH, "rb") as f:
            self.assertEqual(f.read(), self.rules_bytes)
        version, rules = jc.load_sentinels()
        self.assertEqual((version, len(rules)), ("1", 14))

    def test_clean_battle_no_draft(self):
        bd = make_battle(self.tmp, findings=[fd_row(1, exploit="verified")],
                         timeline=[], settle="recall=1.0 (1/1)\n")
        out = os.path.join(self.tmp, "out2")
        rep = D.distill_battle(bd, out=out, knowledge_dir=kdir(self.tmp))
        self.assertEqual(rep["counts"]["sentinel_drafts"], 0)
        self.assertFalse(os.path.isdir(os.path.join(out, "sentinel-staging")))

    def test_draft_deterministic(self):
        tl = [tl_row("2026-10-20T11:00:00Z", "replay:FD-r1-0002:REJECTED")]
        bd = make_battle(self.tmp, findings=[fd_row(2, exploit="verified")],
                         timeline=tl, settle="")
        o1, o2 = os.path.join(self.tmp, "a"), os.path.join(self.tmp, "b")
        D.distill_battle(bd, out=o1, knowledge_dir=kdir(self.tmp))
        D.distill_battle(bd, out=o2, knowledge_dir=kdir(self.tmp))
        p1 = os.path.join(o1, "sentinel-staging", "battle-1--sentinel-drafts.tsv")
        p2 = os.path.join(o2, "sentinel-staging", "battle-1--sentinel-drafts.tsv")
        with open(p1, "rb") as f1, open(p2, "rb") as f2:
            self.assertEqual(f1.read(), f2.read(), "同输入两跑逐字节一致")


if __name__ == "__main__":
    unittest.main()
