# -*- coding: utf-8 -*-
"""W1-T6：VulnClaw 插槽适配器（F3）——四件消费纪律的引擎面单测。

夹具=docs/research/vulnclaw-live-trial.md §10 glm-4.7 真实会话样本
（20261017_003221_http___localhost_3081.json 修剪版：final_answer/
verified_claims/findings/task_constraints 原样保留，重型 evidence content
裁掉——shape 真值不变）。四件对应 §10.4 上线前置：
① 消费 final_answer+verified_claims，findings[] 只当线索队列（§10.2④a）
② 副作用黑名单（删库/关机/外发）进 TaskConstraints 预筛（§10.2④b）
③ 成本走网关侧 usage 外挂回填（§9.5/§10.4④——引擎内建计量不可信）
④ 绕 P0#2 findings 组装崩溃（§9.6/§10.4①——int 形状容忍+手动 report 路径）
"""
import json, os, re, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
ADAPTER = os.path.join(ROOT, "engines", "vulnclaw", "adapter.py")
FIX = os.path.join(HERE, "fixtures", "engine", "vulnclaw-session")

sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import registry  # noqa: E402

# 接线面=web-blackbox 引擎同款 KNOWN 并集（registry.all_commands() ∪ 入口挂载面）
KNOWN = registry.all_commands() | {
    "tanyin-guard", "tanyin-canary", "tanyin-egress", "tanyin-redact",
    "tanyin-budgetctl", "tanyin-phases", "tanyin-ledger",
    "tanyin-report", "tanyin-viz", "tanyin-replay",
    "tanyin-knowledge",
}

class VulnclawAdapterBase(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()

    def adapt(self, *extra):
        return subprocess.run([sys.executable, ADAPTER, "--intent-id", "INT-g1-0200",
                               "--out-dir", self.out] + list(extra),
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def sub(self):
        with open(os.path.join(self.out, "submission.json"), encoding="utf-8") as f:
            return json.load(f)

    def log(self):
        with open(os.path.join(self.out, "operations.log"), encoding="utf-8") as f:
            return f.read()


class TestFinalAnswerConsumption(VulnclawAdapterBase):
    """① FINAL 实证发现→findings；规则层 findings[]→vuln-clue 线索；否定结果→facts。"""

    def adapt_main(self):
        return self.adapt("--session", os.path.join(FIX, "session.json"),
                           "--usage-file", os.path.join(FIX, "usage-gateway.json"))

    def test_submission_schema_conform(self):
        r = self.adapt_main()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sub = self.sub()
        for f in ("intent_id", "engine", "status", "facts", "findings", "assets",
                  "edges", "creds", "operations_log"):
            self.assertIn(f, sub)
        self.assertEqual(sub["engine"], "vulnclaw")
        self.assertEqual(sub["status"], "done")
        self.assertTrue(os.path.isfile(os.path.join(self.out, "operations.log")))
        self.assertIn("findings=5", r.stdout, "收尾行须报 FINAL 发现数")

    def test_final_answer_five_findings(self):
        """§10.2②：5 条实证发现（F1-F5）全部来自 final_answer 解析，证据引用随行。"""
        self.adapt_main()
        sub = self.sub()
        self.assertEqual(len(sub["findings"]), 5)
        by_key = {f["dedup_key_proposed"]: f for f in sub["findings"]}
        for n in range(1, 6):
            self.assertIn("F%d-" % n, " ".join(by_key))
        f1 = next(f for f in sub["findings"] if "F1-" in f["dedup_key_proposed"])
        self.assertIn("Vite", f1["title"])
        self.assertEqual(f1["impact"], "低", "Low→低")
        self.assertEqual(f1["confidence"], "C2")
        self.assertEqual(f1["exploitation_status"], "verified")
        refs = " ".join(f1["evidence_refs"])
        self.assertIn("e005", refs, "e005–e009 区间须展开")
        self.assertIn("e009", refs)
        steps = "\n".join(f1["reproducible_steps"])
        self.assertIn("/@vite/client", steps, "复现步骤携带真实请求路径")
        f3 = next(f for f in sub["findings"] if "F3-" in f["dedup_key_proposed"])
        self.assertEqual(f3["impact"], "低", "Info→低")
        self.assertEqual(f3["location"], "/api/health")
        self.assertTrue(f3["reproducible_steps"], "步骤非空")
    def test_rule_layer_findings_demoted_to_lead_queue(self):
        """§10.2④a：findings[] 规则层候选（[自动] 模板碎片）只当线索队列，不成 finding。"""
        self.adapt_main()
        sub = self.sub()
        self.assertFalse([f for f in sub["findings"] if "[自动]" in f["title"]],
                         "规则层候选不得进 findings")
        leads = [f for f in sub["facts"] if f["kind"] == "vuln-clue"]
        self.assertEqual(len(leads), 4, "4 条 [自动] 候选全部降权为线索")
        self.assertIn("线索", leads[0]["detail"])
        blob = " ".join(f["detail"] for f in leads)
        for kw in ("SQL注入", "XSS", "文件包含", "弱口令"):
            self.assertIn(kw, blob, "候选类型须保留可读：" + kw)

    def test_negative_results_and_claims_as_facts(self):
        """否定结果（§10.2② 往往更值钱）+ verified_claims + 约束审计→facts。"""
        self.adapt_main()
        sub = self.sub()
        neg = " ".join(f["detail"] for f in sub["facts"] if "否定结果" in f["detail"])
        for kw in ("SQLi", "路径遍历", "匿名访问", "弱密码", "会话熵"):
            self.assertIn(kw, neg, "否定结果缺 " + kw)
        claim = [f for f in sub["facts"] if "c001" in f["detail"]]
        self.assertTrue(claim, "verified_claim c001 须落 fact")
        self.assertIn("e005", claim[0]["detail"])
        audit = " ".join(f["detail"] for f in sub["facts"] if "task_constraints" in f["detail"])
        self.assertIn("3081", audit)
        self.assertIn("violations=0", audit)
        overview = " ".join(f["detail"] for f in sub["facts"] if "solve 概况" in f["detail"])
        self.assertIn("tool_calls=33", overview)
        self.assertIn("evidence=21", overview)

    def test_assets_endpoint_map(self):
        """端点图谱（§9.4 情报层 1/1 成立）→ endpoint 资产。"""
        self.adapt_main()
        sub = self.sub()
        vals = [a["value"] for a in sub["assets"]]
        self.assertIn("http://localhost:3081", vals, "目标本体=app 资产")
        eps = [v for v in vals if v.endswith("/api/health")]
        self.assertTrue(eps, "F3 位置须落 endpoint 资产")


class TestUsageBackfill(VulnclawAdapterBase):
    """③ 网关侧 usage 外挂回填：token/requests/dollars 求和入账，不采信引擎内建计量。"""

    def test_gateway_records_summed(self):
        r = self.adapt("--session", os.path.join(FIX, "session.json"),
                       "--usage-file", os.path.join(FIX, "usage-gateway.json"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sub = self.sub()
        usage = " ".join(f["detail"] for f in sub["facts"] if "usage-backfill" in f["detail"])
        self.assertIn("token=109607", usage)
        self.assertIn("requests=34", usage)
        self.assertIn("网关侧", usage)
        art = os.path.join(self.out, "artifacts", "usage-backfill.json")
        self.assertTrue(os.path.isfile(art), "usage 外挂原件归档 artifacts/")
        self.assertIn("usage-backfill", self.log())

    def test_alt_key_format_prompt_completion(self):
        """prompt_tokens/completion_tokens 别键形→求和口径一致（容错映射）。"""
        r = self.adapt("--session", os.path.join(FIX, "session.json"),
                       "--usage-file", os.path.join(FIX, "usage-gateway-alt.json"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sub = self.sub()
        usage = " ".join(f["detail"] for f in sub["facts"] if "usage-backfill" in f["detail"])
        self.assertIn("token=1800", usage)
        self.assertIn("requests=2", usage)

    def test_absent_usage_noted_honestly(self):
        """未提供外挂→如实记缺位（成本核算不静默归零）。"""
        r = self.adapt("--session", os.path.join(FIX, "session.json"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sub = self.sub()
        self.assertTrue([f for f in sub["facts"] if "usage 外挂缺位" in f["detail"]])
        self.assertIn("不采信", self.log())

class TestBlacklistPrefilter(VulnclawAdapterBase):
    """② 副作用黑名单（删库/关机/外发）进 TaskConstraints 预筛——结构化执法不走 prompt 措辞。"""

    def adapt_run(self, goal, vulnclaw="/nonexistent/vulnclaw"):
        return self.adapt("--run", "--target", "http://localhost:3081", "--goal", goal,
                          "--vulnclaw", vulnclaw)

    def test_goal_hit_blocks_before_launch(self):
        r = self.adapt_run("先删库 DROP DATABASE 再关机重启服务器")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sub = self.sub()
        self.assertEqual(sub["status"], "blocked")
        self.assertEqual(sub["findings"], [])
        log = self.log()
        self.assertIn("blacklist: HIT", log)
        self.assertIn("删库", log)
        self.assertIn("关机", log)

    def test_clean_goal_passes_prefilter(self):
        """干净 goal 不被黑名单拦——落到下一道环境门（二进制缺失=blocked）。"""
        r = self.adapt_run("授权靶场只读安全评估：仅信息收集")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sub = self.sub()
        self.assertEqual(sub["status"], "blocked")
        self.assertNotIn("blacklist: HIT", self.log())
        self.assertIn("vulnclaw-missing", r.stdout)

    def test_constraints_artifact_shape(self):
        """task-constraints.json=VulnClaw TaskConstraints 11 键形状+黑名单三类动作。"""
        self.adapt_run("授权靶场只读安全评估")
        p = os.path.join(self.out, "task-constraints.json")
        self.assertTrue(os.path.isfile(p), "结构化通道工件须落盘")
        with open(p, encoding="utf-8") as f:
            c = json.load(f)
        for k in ("allowed_ports", "blocked_ports", "allowed_hosts", "blocked_hosts",
                  "allowed_paths", "blocked_paths", "allowed_actions",
                  "blocked_actions", "notes", "strict_mode"):
            self.assertIn(k, c)
        self.assertEqual(c["allowed_ports"], [3081], "目标端口自动入 allowed")
        self.assertEqual(c["allowed_hosts"], ["localhost"])
        for port in (8900, 3000, 8787, 8443):
            self.assertIn(port, c["blocked_ports"], "禁碰端口结构化落地")
        for act in ("drop-database", "shutdown-host", "exfiltrate-data"):
            self.assertIn(act, c["blocked_actions"], "副作用黑名单缺 " + act)
        self.assertTrue(c["notes"])
        self.assertTrue(c["strict_mode"])


class TestP02Bypass(VulnclawAdapterBase):
    """④ 绕 P0#2：int 形状 verified_claims 容忍（上游 cli/main.py:1609 会崩）+
    complete 事件缺席识别→手动归一路径（等价手动 vulnclaw report）。"""

    def test_int_shaped_claims_tolerated(self):
        r = self.adapt("--session", os.path.join(FIX, "session-p02-summary.json"),
                       "--events-file", os.path.join(FIX, "stream-no-complete.ndjson"))
        self.assertEqual(r.returncode, 0, "P0#2 形状不得让适配器崩（上游崩点）")
        sub = self.sub()
        self.assertEqual(sub["status"], "done")
        self.assertEqual(len(sub["findings"]), 5, "final_answer 消费不受 int 形状影响")
        log = self.log()
        self.assertIn("P0#2", log)
        self.assertIn("int", log, "log 须点名 int 计数形状（get_summary 侧）")

    def test_missing_complete_event_triggers_bypass_note(self):
        r = self.adapt("--session", os.path.join(FIX, "session.json"),
                       "--events-file", os.path.join(FIX, "stream-no-complete.ndjson"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("P0#2 绕过", self.log())
        self.assertIn("complete", self.log())
        self.assertEqual(self.sub()["status"], "done")

    def test_complete_event_present_no_bypass_note(self):
        """阴性对照：complete 事件在场→不记绕过。"""
        r = self.adapt("--session", os.path.join(FIX, "session.json"),
                       "--events-file", os.path.join(FIX, "stream-complete.ndjson"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("P0#2 绕过", self.log())

class TestArgvAndWiring(unittest.TestCase):
    """argv 契约（T5 裁决②同款）+registry 接线（MANIFEST 面）。"""

    def test_usage_error_exit_2(self):
        r = subprocess.run([sys.executable, ADAPTER], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 2)
        self.assertIn("用法", r.stderr)

    def test_manifest_fields(self):
        eng = os.path.join(ROOT, "engines", "vulnclaw")
        with open(os.path.join(eng, "MANIFEST.md"), encoding="utf-8") as f:
            text = f.read()
        for fld in ("name", "kind", "version", "适用场景", "参数", "产物路径", "超时",
                    "重试策略", "幂等键", "纪律能力声明", "工具依赖", "验签公钥"):
            self.assertIn(fld, text, "MANIFEST 缺字段 " + fld)
        self.assertIn("kind: cli", text)
        self.assertIn("vulnclaw", text)

    def test_referenced_commands_known(self):
        """registry 接线：引擎 md 面 tanyin-* 引用 ⊆ 已知命令面（selfcheck ①同律）。"""
        eng = os.path.join(ROOT, "engines", "vulnclaw")
        for dirpath, _dirs, files in os.walk(eng):
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                    text = f.read()
                for m in re.finditer(r"(?:ledger-|tanyin-)([a-z][a-z0-9-]*)", text):
                    self.assertIn(m.group(0).rstrip("-"), KNOWN | registry.all_commands(),
                                  "%s 引用未知命令: %s" % (fn, m.group(0)))


if __name__ == "__main__":
    unittest.main()
