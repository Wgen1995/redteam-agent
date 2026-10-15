# -*- coding: utf-8 -*-
"""OP1（2026-10-14 旧欠清理批）：rate 入执法面 + DENYLIST v2 + nuclei 固化。

来源：docs/reviews/2026-10-10-nine-expert-review/02-opsec.md 缺口 1/3 与可执行建议表
（「budgetctl rate 接入 gate_chain+P0 八问⑥必填」「DENYLIST v2+nuclei 固化
-rl 50 -etags dos,intrusive」）——审计判词「内功九段外功一段」，本批补外功：

- rate：budgetctl rate 滑窗熔断（查询面代码已有）接入 tanyin-guard gate_chain
  执法位（每次 exec/inject 前置核速）+ budgetctl enforce 派发门必填
  goals.rate_limit（P0 八问⑥——「预算必须是代码不是话术」）。
- 滑窗单源=ledger.enforce.rate_window/parse_rate/parse_ts（budgetctl 与 guard
  共用，防两份漂移——deny/scope 单源同律）。
- DENYLIST v2：DoS 工具/激进档/BENCHMARK 型模式补入（slowloris/hulk/goldeneye
  调用形态锚定——文档字样不误伤）；两份同步律（shared/DENYLIST.md 与
  enforce.DENY_EMBEDDED 同改）由本文件+test_enforce_unit 双钉。
- nuclei：调用模板固化 -rl 50 -etags dos,intrusive（engines/nuclei/adapter.py）
  + guard 执行通道机械执法（缺参=REJECT，防绕过）。
"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))

from ledger import core, enforce  # noqa: E402

GUARD = os.path.join(ROOT, "cli", "tanyin-guard")
BUDGETCTL = os.path.join(ROOT, "cli", "tanyin-budgetctl")
ADAPTER = os.path.join(ROOT, "engines", "nuclei", "adapter.py")
DENYLIST_MD = os.path.join(ROOT, "shared", "DENYLIST.md")
FIX = os.path.join(HERE, "fixtures", "G-g1")
PY = sys.executable
TAB = chr(9)

# 单元面合成 goals 行（19 列，契约 01 §3.1）：第 9 列=rate_limit。
GOALS_ROW = ["G-op1-0001", "t.example", "op1 单源滑窗", "auth/x.pdf", "a" * 64, "s",
             "2026-09-01", "2026-09-30", "600/10m", "09:00-19:00", "ops@x.example",
             "2M;50000;40", "0", "zh", "ctx", "strong", "T3", "2", "2026-09-01T00:00:00Z"]


def _goal_dir(case, name="G-op1"):
    td = tempfile.TemporaryDirectory()
    case.addCleanup(td.cleanup)
    return shutil.copytree(FIX, os.path.join(td.name, name))


def _set_rate(gd, val):
    """goals.tsv 首行 rate_limit 列（第 9 列）改写——镜像 BudgetRate 夹具手法。"""
    gp = os.path.join(gd, "goals.tsv")
    with open(gp, encoding="utf-8") as f:
        cells = f.read().splitlines()[0].split(TAB)
    cells[8] = val
    with open(gp, "w", encoding="utf-8", newline=chr(10)) as f:
        f.write(TAB.join(cells) + chr(10))


def _budget_append(gd, ts, requests):
    with open(os.path.join(gd, "budget.tsv"), "a", encoding="utf-8", newline=chr(10)) as f:
        f.write(TAB.join([ts, "0", str(requests), "0", "0", "goal", "op1-burst", "2"]) + chr(10))


def _guard(gd, ts, *cmd, **kw):
    return subprocess.run([PY, GUARD, "exec", "--goal-dir", gd, "--timestamp=" + ts, "--"] + list(cmd),
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=kw.get("env"))


def _budgetctl(*args):
    return subprocess.run([PY, BUDGETCTL] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def _timeline(gd):
    return open(os.path.join(gd, "timeline.tsv"), encoding="utf-8").read()


def _nuclei_shim(case):
    """PATH 前置 nuclei 替身（exit 0）——过门即可，零真实扫描（R-T4-2 同律）。"""
    d = tempfile.mkdtemp(prefix="op1-nuclei-")
    case.addCleanup(shutil.rmtree, d, True)
    p = os.path.join(d, "nuclei")
    with open(p, "w", encoding="utf-8", newline=chr(10)) as f:
        f.write("#!/bin/sh" + chr(10) + "exit 0" + chr(10))
    os.chmod(p, 0o755)
    env = dict(os.environ)
    env["PATH"] = d + os.pathsep + env.get("PATH", "")
    return env


class RateWindowUnit(unittest.TestCase):
    """enforce 单源滑窗（OP1）：parse_rate/parse_ts/rate_window 四态+窗口语义。"""

    def _session(self, rate, budget=()):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        gd = td.name
        row = list(GOALS_ROW)
        row[8] = rate
        with open(os.path.join(gd, "goals.tsv"), "w", encoding="utf-8", newline=chr(10)) as f:
            f.write(TAB.join(row) + chr(10))
        if budget:
            with open(os.path.join(gd, "budget.tsv"), "w", encoding="utf-8", newline=chr(10)) as f:
                for ts, req in budget:
                    f.write(TAB.join([ts, "0", str(req), "0", "0", "goal", "op1", "2"]) + chr(10))
        return core.Session(gd)

    def test_parse_rate_forms(self):
        self.assertEqual(enforce.parse_rate("600/10m"), (600.0, 600))
        self.assertEqual(enforce.parse_rate("50/1s"), (50.0, 1))   # 窗口须带数值（裸单位 "50/s" 非法=既有语义，单源迁移零变更）
        self.assertEqual(enforce.parse_rate("2k/2h"), (2000.0, 7200))
        self.assertEqual(enforce.parse_rate("300"), (300.0, 0))
        with self.assertRaises(ValueError):
            enforce.parse_rate("abc/10m")

    def test_window_over_and_ok(self):
        w = enforce.rate_window(self._session("600/10m", [("2026-09-23T02:00:00Z", 25),
                                                          ("2026-09-23T02:05:00Z", 700)]),
                                enforce.parse_ts("2026-09-23T02:06:00Z"))
        self.assertEqual(w["state"], "over")
        self.assertEqual(w["used"], 725.0)
        self.assertEqual(w["limit"], 600.0)
        self.assertEqual(w["window"], 600)
        w2 = enforce.rate_window(self._session("600/10m", [("2026-09-23T02:00:00Z", 25),
                                                           ("2026-09-23T02:05:00Z", 100)]),
                                 enforce.parse_ts("2026-09-23T02:06:00Z"))
        self.assertEqual(w2["state"], "ok")
        self.assertEqual(w2["used"], 125.0)

    def test_window_left_open_right_closed(self):
        """窗（now-window, now]：左边界时刻不计入（budgetctl 既有语义钉死）。"""
        w = enforce.rate_window(self._session("600/10m", [("2026-09-23T01:56:00Z", 999),
                                                          ("2026-09-23T02:05:00Z", 10)]),
                                enforce.parse_ts("2026-09-23T02:06:00Z"))
        self.assertEqual(w["state"], "ok")
        self.assertEqual(w["used"], 10.0)

    def test_window_unset_and_bad_states(self):
        self.assertEqual(enforce.rate_window(self._session(""))["state"], "unset")
        self.assertEqual(enforce.rate_window(self._session("abc"))["state"], "bad-limit")
        w = enforce.rate_window(self._session("600/10m", [("not-a-ts", 5)]))
        self.assertEqual(w["state"], "bad-stamp")

    def test_window_default_anchor_is_latest_stamp(self):
        """now 缺省=账本最新流水时间（可重放口径，budgetctl rate 同锚单源）。"""
        w = enforce.rate_window(self._session("600/10m", [("2026-09-23T02:00:00Z", 25),
                                                          ("2026-09-23T02:05:00Z", 700)]))
        self.assertEqual(w["state"], "over")
        self.assertEqual(w["used"], 725.0)

    def test_single_source_no_local_copies(self):
        """滑窗单源钉：budgetctl 不得再本地定义 parse_rate/parse_ts（防两份漂移）。"""
        with open(BUDGETCTL, encoding="utf-8") as f:
            src = f.read()
        self.assertIn("from ledger.enforce import", src)
        self.assertNotRegex(src, r"(?m)^def parse_rate", "budgetctl 仍有本地 parse_rate")
        self.assertNotRegex(src, r"(?m)^def parse_ts", "budgetctl 仍有本地 parse_ts")


class RateGateGuard(unittest.TestCase):
    """gate_chain rate 执法位（OP1）：超窗=REJECT 落账；未申报不在本门拦（必填在派发门）。"""

    def test_over_limit_rejected_with_timeline(self):
        gd = _goal_dir(self)
        _budget_append(gd, "2026-09-23T02:05:00Z", 700)   # 窗内 25+700=725 > 600
        r = _guard(gd, "2026-09-23T02:06:00Z", PY, "-c", "pass", "ping", "api.shop.example")
        self.assertEqual(r.returncode, 1, "超窗执行须 REJECT: " + r.stdout + r.stderr)
        self.assertIn("rate-limit", r.stdout)
        self.assertIn("used=725", r.stdout)
        tl = _timeline(gd)
        self.assertIn("guard-reject rate-limit used=725", tl)
        self.assertIn("limit=600", tl)
        ok, _line = core.Session(gd).verify_chain()
        self.assertTrue(ok, "rate REJECT 落账后链须完整")

    def test_within_limit_passes_with_ticket(self):
        gd = _goal_dir(self)
        _budget_append(gd, "2026-09-23T02:05:00Z", 100)   # 窗内 25+100=125 <= 600
        r = _guard(gd, "2026-09-23T02:06:00Z", PY, "-c", "pass", "ping", "api.shop.example")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("request-ticket", _timeline(gd).splitlines()[-1])

    def test_scope_gate_fires_before_rate(self):
        """链序钉死：deny→nuclei→scope→permitted→rate——界外主机先被 scope 拦。"""
        gd = _goal_dir(self)
        _budget_append(gd, "2026-09-23T02:05:00Z", 700)
        r = _guard(gd, "2026-09-23T02:06:00Z", PY, "-c", "pass", "ping", "evil.example")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("界外目标", r.stdout)
        self.assertIn("guard-reject out-of-scope", _timeline(gd))

    def test_unset_rate_limit_not_gated_here(self):
        """未申报=本门不设限（fail-closed 于派发门 budgetctl enforce 拦，见下类）——
        既有查询面 env 语义沿用，零破坏过渡面如实钉死。"""
        gd = _goal_dir(self)
        _set_rate(gd, "")
        _budget_append(gd, "2026-09-23T02:05:00Z", 700)
        r = _guard(gd, "2026-09-23T02:06:00Z", PY, "-c", "pass", "ping", "api.shop.example")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class RateRequiredAtDispatch(unittest.TestCase):
    """P0 八问⑥必填（OP1）：budgetctl enforce 派发门拒未申报/不可解析 rate_limit。"""

    def test_enforce_rejects_unset(self):
        gd = _goal_dir(self)
        _set_rate(gd, "")
        r = _budgetctl("enforce", "--goal-dir", gd, "--intent-id=INT-g1-0002",
                       "--timestamp=2026-09-23T06:00:00Z")
        self.assertEqual(r.returncode, 1, "rate_limit 未申报须拒派: " + r.stdout + r.stderr)
        self.assertIn("rate-limit-unset", r.stdout)
        self.assertIn("budgetctl-reject", _timeline(gd))
        ok, _line = core.Session(gd).verify_chain()
        self.assertTrue(ok)

    def test_enforce_rejects_unparseable(self):
        gd = _goal_dir(self)
        _set_rate(gd, "abc")
        r = _budgetctl("enforce", "--goal-dir", gd, "--intent-id=INT-g1-0002",
                       "--timestamp=2026-09-23T06:00:00Z")
        self.assertEqual(r.returncode, 1, "rate_limit 不可解析须拒派: " + r.stdout + r.stderr)
        self.assertIn("rate-limit-bad", r.stdout)

    def test_enforce_passes_when_declared(self):
        gd = _goal_dir(self)   # G-g1 原样：rate_limit=600/10m 已申报
        r = _budgetctl("enforce", "--goal-dir", gd, "--intent-id=INT-g1-0002",
                       "--timestamp=2026-09-23T06:00:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith("OK"))


class DenyListV2(unittest.TestCase):
    """DENYLIST v2（OP1）：DoS 工具/激进档/BENCHMARK 型——调用形态锚定+两份同步律。"""

    V2 = ("slowloris.py", "slowloris.pl", "hulk.py", "goldeneye.py", "torshammer.py",
          "slowhttptest -d", "-T5", "--risk=3", "--level=5", "ab -n", "hey -z",
          "siege -c", "wrk -t")

    def test_v2_patterns_in_both_copies(self):
        for p in self.V2:
            self.assertIn(p, enforce.DENY_EMBEDDED, "内嵌兜底缺 v2 模式: " + p)
        with open(DENYLIST_MD, encoding="utf-8") as f:
            pats = enforce.parse_denylist(f.read())
        for p in self.V2:
            self.assertIn(p, pats, "DENYLIST.md 缺 v2 模式: " + p)
        self.assertEqual(pats, enforce.DENY_EMBEDDED, "两份同步律（OP1 再钉）")

    def test_dos_tool_and_aggressive_tier_hit(self):
        for cmd in (["python3", "slowloris.py", "-d", "https://x"],
                    ["python3", "hulk.py", "https://x"],
                    ["python3", "goldeneye.py", "https://x", "-s", "100"],
                    ["torshammer.py", "-t", "5", "x"],
                    ["slowhttptest", "-d", "x", "-c", "100"],
                    ["nmap", "-sS", "-T5", "x"],
                    ["nmap", "-T5", "-sS", "x"],
                    ["ab", "-n", "10000", "-c", "100", "https://x"],
                    ["hey", "-z", "30s", "https://x"],
                    ["wrk", "-t", "12", "-c", "400", "https://x"],
                    ["siege", "-c", "100", "-t", "1m", "x"],
                    ["sqlmap", "--risk=3", "-u", "x"],
                    ["sqlmap", "-u", "x", "--level=5"]):
            self.assertIsNotNone(enforce.deny_hit(" ".join(cmd)), "v2 应命中: %r" % (cmd,))

    def test_doc_mentions_not_hit(self):
        """文档命令含工具字样不误伤（调用形态锚定的意义所在）。"""
        for cmd in ("cat hulk-notes.md", "grep -i hulk report.txt", "cat goldeneye-复盘.md",
                    "cat slowloris-缓解笔记.md", "cat torshammer.md",
                    "cat slowhttptest-notes.md", "cat report.txt", "ls -la"):
            self.assertIsNone(enforce.deny_hit(cmd), "误伤: " + cmd)

    def test_guard_rejects_dos_tool_exec(self):
        gd = _goal_dir(self)
        r = _guard(gd, "2026-09-30T12:00:00Z", "python3", "hulk.py", "http://api.shop.example/")
        self.assertEqual(r.returncode, 1, "DoS 工具经执行通道须 REJECT: " + r.stdout + r.stderr)
        self.assertIn("deny-list", r.stdout)


class NucleiHardening(unittest.TestCase):
    """nuclei 固化（OP1）：调用模板 -rl 50 -etags dos,intrusive + 执行通道机械执法。"""

    def test_adapter_pins_rate_and_etags(self):
        with open(ADAPTER, encoding="utf-8") as f:
            src = f.read()
        self.assertIn('"-rl"', src, "调用模板缺 -rl")
        self.assertIn('"-etags"', src, "调用模板缺 -etags")
        self.assertIn('"dos,intrusive"', src, "etags 固化值缺 dos,intrusive")

    def test_unit_params_check(self):
        self.assertIn("-rl", enforce.nuclei_params_ok(["nuclei", "-u", "x"]))
        self.assertIn("-etags", enforce.nuclei_params_ok(["nuclei", "-rl", "50", "-u", "x"]))
        self.assertIsNone(enforce.nuclei_params_ok(
            ["nuclei", "-rl", "50", "-etags", "dos,intrusive", "-u", "x"]))
        self.assertIsNone(enforce.nuclei_params_ok(["curl", "http://x/"]),
                          "非 nuclei 命令不检查")

    def test_gate_rejects_nuclei_without_params(self):
        if os.name == "nt":
            self.skipTest("PATH 替身仅 POSIX")
        gd = _goal_dir(self)
        env = _nuclei_shim(self)
        r = subprocess.run(
            [PY, GUARD, "exec", "--goal-dir", gd, "--timestamp=2026-09-30T12:00:00Z", "--",
             "nuclei", "-jsonl", "-u", "http://api.shop.example/"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        self.assertEqual(r.returncode, 1, "缺 -rl/-etags 的 nuclei 须 REJECT: " + r.stdout + r.stderr)
        self.assertIn("nuclei", r.stdout)
        self.assertIn("-etags", r.stdout)
        self.assertIn("guard-reject nuclei-params", _timeline(gd))

    def test_gate_passes_nuclei_with_params(self):
        if os.name == "nt":
            self.skipTest("PATH 替身仅 POSIX")
        gd = _goal_dir(self)
        env = _nuclei_shim(self)
        r = subprocess.run(
            [PY, GUARD, "exec", "--goal-dir", gd, "--timestamp=2026-09-30T12:00:00Z", "--",
             "nuclei", "-jsonl", "-rl", "50", "-etags", "dos,intrusive",
             "-u", "http://api.shop.example/"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        self.assertEqual(r.returncode, 0, "带固化参数的 nuclei 须过门: " + r.stdout + r.stderr)
        self.assertIn("request-ticket", _timeline(gd).splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
