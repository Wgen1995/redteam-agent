# -*- coding: utf-8 -*-
"""OP2（docs/superpowers/plans/2026-10-14-opsec-wallclock.md Task OP2；
审计 docs/reviews/2026-10-10-nine-expert-review/02-opsec.md 缺口#1/建议表）：
UA 治理 + request-ticket full argv。

审计判词：UA 自报家门（tanyin/1、probe/1.2、tanyin-replay/1——一条 IDS 规则全量
归因）；request-ticket 只记 cmd[0]+argc——full argv 不落账，流量画像不可重建。

三面：
1. replay 出站 UA 治理（localhost mock 服务实测捕获）：
   - 卡片自名 UA → 中性默认（NEUTRAL_UA 单源）；
   - --ua 显式覆盖一切；TANYIN_UA env 配置默认值；
   - 第三方 UA（Mozilla 形）保真透传（重放保真不归因）；缺 UA 头补中性默认。
2. request-ticket 升级 tokenize 脱敏 full argv：
   - 全 argv token 落账（cmd[0] 之外的参数旧格式从不落账=红面）；
   - vault 真值复用 tokenize_output 长值优先替换脱敏；占位形降格 <cred-N>
     （timeline 事件列不在 special.py {{vault:}} 占位符白名单——冻结口径防
     redact-scan 误报）；TAB/换行清洗防 TSV 列破格。
3. 仓内自名 UA 点位清零扫描（单源复用 ledger.ua.SELF_UA_RE）：
   - 源码目录 + evidence 卡（可重放请求模板）grep 零自名 UA；
   - 冻结战斗工件（artifacts/submissions——content_hash 钉死的历史证据）不在
     清洗面：改写即断账本哈希链，出站执法已在 replay 层根治（计划口径「grep
     自报点位」限于会外发的点位文件）。docs 引文（审计/计划原文）同不扫。
"""
import http.server, json, os, re, shutil, socketserver, subprocess, sys, tempfile, threading, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
CLI = os.path.join(ROOT, "cli")
REPLAY = os.path.join(CLI, "tanyin-replay")
GUARD = os.path.join(CLI, "tanyin-guard")
LEDGER = os.path.join(CLI, "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-10-14T10:00:00Z"
PY = sys.executable

sys.path.insert(0, CLI)
from ledger import ua as ua_mod  # noqa: E402

SECRET = "OP2vault-Truth-9812"


def read_text(p):
    with open(p, encoding="utf-8", errors="ignore") as f:
        return f.read()


def write_text(p, text):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def run_replay(gd, *args, **kw):
    return subprocess.run([PY, REPLAY, "replay", "--goal-dir", gd] + list(args),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", **kw)


def run_guard(gd, *cmd):
    return subprocess.run([PY, GUARD, "exec", "--goal-dir", gd,
                           "--timestamp=" + TS, "--"] + list(cmd),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


class _Capture(http.server.BaseHTTPRequestHandler):
    """mock 目标：200/ok，捕获到达的 User-Agent（OP2 实测面非纸上断言）。"""
    captured = []

    def do_GET(self):
        _Capture.captured.append(self.headers.get("User-Agent", ""))
        body = "ok"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *a):
        pass


class TestReplayUAGovernance(unittest.TestCase):
    """面 1：replay 出站 UA 治理——自名归零、--ua/env 可配、第三方保真。"""

    @classmethod
    def setUpClass(cls):
        cls.srv = socketserver.TCPServer(("127.0.0.1", 0), _Capture)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.gd = os.path.join(self.tmp, "G-g1")
        shutil.copytree(FIX, self.gd)
        r = subprocess.run([PY, LEDGER, "add-scope", "--goal-dir", self.gd,
                            "--kind=include", "--matcher=127.0.0.0/8",
                            "--timestamp=" + TS],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _Capture.captured = []

    def _mint_card(self, ua=None):
        """预铸 E-index 首行卡片（test_replay_driver 同构；UA 可选注入）。"""
        ev = [l.split("\t")[0] for l in read_text(os.path.join(self.gd, "E-index.tsv")).splitlines() if l][0]
        lines = ["---", "id: %s" % ev, "network_position: internet", "raw_request: |",
                 "  GET /ok HTTP/1.1", "  Host: 127.0.0.1"]
        if ua is not None:
            lines.append("  User-Agent: " + ua)
        lines += ["  Connection: close", "expected: {}", "pair_group: ", "---", "## 摘", ""]
        card = os.path.join(self.gd, "evidence", ev + ".md")
        os.makedirs(os.path.dirname(card), exist_ok=True)
        write_text(card, "\n".join(lines))
        return ev

    def _replay(self, ev, *extra, **kw):
        r = run_replay(self.gd, "--id=" + ev, "--scheme=http",
                       "--port=%d" % self.port, "--timeout=3",
                       "--timestamp=" + TS, *extra, **kw)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(_Capture.captured, "请求未到达 mock 目标")
        return _Capture.captured[-1]

    def test_self_named_card_ua_neutralized(self):
        ev = self._mint_card("tanyin/1")
        got = self._replay(ev)
        self.assertEqual(got, ua_mod.NEUTRAL_UA, "自名 UA 必须替换为中性默认")

    def test_self_named_probe_family_neutralized(self):
        for bad in ("probe/1.2", "tanyin-replay/1", "tanyin-probe/1.0", "replay/1"):
            _Capture.captured = []
            ev = self._mint_card(bad)
            got = self._replay(ev)
            self.assertEqual(got, ua_mod.NEUTRAL_UA, "自名家族须中性化: " + bad)

    def test_ua_flag_overrides(self):
        ev = self._mint_card("tanyin/1")
        self.assertEqual(self._replay(ev, "--ua=CustomAgent/9"), "CustomAgent/9")

    def test_env_configures_neutral_default(self):
        ev = self._mint_card("tanyin-probe/1.0")
        r = run_replay(self.gd, "--id=" + ev, "--scheme=http",
                       "--port=%d" % self.port, "--timeout=3", "--timestamp=" + TS,
                       env=dict(os.environ, TANYIN_UA="EnvUA/2"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(_Capture.captured[-1], "EnvUA/2", "TANYIN_UA 须可配默认")

    def test_third_party_ua_preserved(self):
        ev = self._mint_card("Mozilla/5.0 (X11; Linux x86_64)")
        self.assertEqual(self._replay(ev), "Mozilla/5.0 (X11; Linux x86_64)",
                         "第三方 UA 保真透传（重放保真不归因）")

    def test_missing_ua_gets_neutral_default(self):
        ev = self._mint_card(ua=None)
        self.assertEqual(self._replay(ev), ua_mod.NEUTRAL_UA, "缺 UA 头补中性默认")


class TestRequestTicketFullArgv(unittest.TestCase):
    """面 2：request-ticket cmd[0]+argc → tokenize 脱敏 full argv（审计建议表 S 级）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.gd = os.path.join(self.tmp, "G-g1")
        shutil.copytree(FIX, self.gd)

    def _deploy_vault(self):
        r = subprocess.run([PY, GUARD, "deploy-vault", "--goal-dir", self.gd,
                            "--cred=1", "--username=op1", "--timestamp=" + TS],
                           capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, TANYIN_VAULT_SECRET=SECRET,
                                    TANYIN_VAULT_PASSPHRASE="pp-op2"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def _ticket(self):
        tl = read_text(os.path.join(self.gd, "timeline.tsv")).splitlines()
        rows = [l for l in tl if "request-ticket" in l]
        self.assertTrue(rows, "request-ticket 事件须落账")
        return rows[-1]

    def test_full_argv_recorded_beyond_cmd0(self):
        r = run_guard(self.gd, PY, "-c", "pass", "alpha-OP2", "beta-OP2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ev = self._ticket()
        for tok in ("alpha-OP2", "beta-OP2", "-c", "pass"):
            self.assertIn(tok, ev, "full argv 须落账（旧格式 cmd[0]+argc 不含参数）: " + tok)
        self.assertIn("argc=", ev, "argc 保留")

    def test_secret_redacted_via_vault_placeholder_reuse(self):
        self._deploy_vault()
        r = run_guard(self.gd, PY, "-c", "pass", "marker-OP2", SECRET)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ev = self._ticket()
        whole = read_text(os.path.join(self.gd, "timeline.tsv"))
        self.assertNotIn(SECRET, whole, "vault 真值禁入账本（含 timeline 任何行）")
        self.assertIn("<cred-1>", ev, "脱敏位须以 <cred-N> 掩码呈现")
        self.assertIn("marker-OP2", ev, "非密参数照常落账")

    def test_tab_in_argv_keeps_tsv_shape(self):
        r = run_guard(self.gd, PY, "-c", "pass", "x\ty OP2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        last = read_text(os.path.join(self.gd, "timeline.tsv")).splitlines()[-1]
        self.assertEqual(len(last.split("\t")), 8,
                         "argv 内嵌 TAB 不得破 timeline TSV 列结构（新行 8 列）")
        self.assertIn("request-ticket", last)


class TestRepoSelfUANorm(unittest.TestCase):
    """面 3：仓内自名 UA 点位清零——源码目录 + evidence 卡扫描（单源 SELF_UA_RE）。"""

    SRC_DIRS = ["cli", "phases", "engines", "scripts", "hooks", "shared",
                "platform", "contracts", "install"]
    SKIP_NAMES = {".git", "__pycache__", "webui", "node_modules", ".DS_Store"}
    UA_LINE = re.compile(r"(?i)^\s*user-agent\s*:\s*(\S+)")

    def _self_named_hits(self):
        hits = []
        roots = [os.path.join(ROOT, d) for d in self.SRC_DIRS]
        for root in roots:
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in self.SKIP_NAMES]
                for fn in filenames:
                    p = os.path.join(dirpath, fn)
                    if os.path.getsize(p) > 1000000:
                        continue
                    try:
                        text = read_text(p)
                    except OSError:
                        continue
                    for i, ln in enumerate(text.splitlines(), 1):
                        m = self.UA_LINE.match(ln)
                        if m and ua_mod.is_self_named(m.group(1)):
                            hits.append("%s:%d: %s" % (p, i, ln.strip()))
        import glob
        for p in glob.glob(os.path.join(HERE, "fixtures", "*", "evidence", "*.md")):
            for i, ln in enumerate(read_text(p).splitlines(), 1):
                m = self.UA_LINE.match(ln)
                if m and ua_mod.is_self_named(m.group(1)):
                    hits.append("%s:%d: %s" % (p, i, ln.strip()))
        return hits

    def test_no_self_named_ua_in_source_or_cards(self):
        hits = self._self_named_hits()
        self.assertEqual(hits[:8], [], "自名 UA 一处不留（余量 %d 处）: %r" % (len(hits), hits[:8]))

    def test_discriminator_sanity(self):
        """自名判别式锚定：平台家族命中，第三方形态不误伤。"""
        for bad in ("tanyin/1", "probe/1.2", "tanyin-replay/1", "tanyin-probe/1.0",
                    "tanyin-probe", "replay/1", "probe5/1", "w2-probe/1.0",
                    "tanyin-b20-probe", "tanyin-G-r22/probe", "tanyin-wave/2",
                    "tanyin-r6/1.0", "G-r12-drill", "drill-probe", "probe-drill"):
            self.assertTrue(ua_mod.is_self_named(bad), "须判自名: " + bad)
        for ok in ("Mozilla/5.0", "curl/8.9.1", "Wget/1.21", "Go-http-client/1.1",
                   ua_mod.NEUTRAL_UA):
            self.assertFalse(ua_mod.is_self_named(ok), "不得误伤第三方: " + ok)


if __name__ == "__main__":
    unittest.main()
