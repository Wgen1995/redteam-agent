# -*- coding: utf-8 -*-
"""W1 遗留 T3 · W2 serve 收口——tanyin-serve 单命令起 webui + CLI 输出契约。

宪法#3 红字收口: clone 即用 → tanyin-serve start 一条命令起 webui
（自动选口 / 静默后台 / 日志落位 $TANYIN_HOME/serve），对齐 tanyin-* 家族风格。

CLI 输出契约（与 W2b 单源退出码矩阵对齐: rc2 环境 / rc3 黄灯 / gate-error）:
  --json  旗标下 stdout=单个 JSON 对象——json.loads 直读不炸，零装饰行
          （test_ui_craft 的 CLI 版对称钉: 那边钉 CSS 纯净，这边钉 stdout 纯净）。
  退出码  0 成功 / 1 REJECT（start 已在跑·stop·status 未在跑）/
          2 用法·环境（未知子命令/旗标、缺 ledger 目录、端口区间全忙），
          未预期异常同样 rc2 但 stderr 带 gate-error: 前缀（bug 永不伪装 1）/
          3 黄灯（status: stale=状态在而进程亡 / degraded=进程在而端点不应答）。

测试纪律: 全程 TANYIN_HOME 指临时目录（永不碰真 ~/.tanyin）；
端口全部动态取空闲高位口，永不占用 8900/3000/8787/8443（用户常驻面）。

python3 -m unittest tests.test_serve_cli
"""
import http.client
import importlib.machinery
import importlib.util
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli")
SERVE = os.path.join(CLI, "tanyin-serve")
sys.path.insert(0, CLI)
from ledger import core  # noqa: E402

FORBIDDEN_PORTS = {8900, 3000, 8787, 8443}   # 用户常驻服务面: 测试永不触碰
TS1, TS2 = "2026-10-18T01:00:00Z", "2026-10-18T01:05:00Z"


def free_port():
    """取一个空闲高位口（避开禁碰口；仅探测后即释放，存在微小竞态由重试兜）。"""
    for _ in range(20):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        p = s.getsockname()[1]
        s.close()
        if p not in FORBIDDEN_PORTS:
            return p
    raise RuntimeError("20 次探测均撞禁碰口，环境异常")


def _row(tname, **kw):
    r = [""] * len(core.TABLES[tname])
    for k, v in kw.items():
        r[core.TABLES[tname].index(k)] = str(v)
    return r


def _chained_tl(specs):
    """铸链式 timeline 行（test_v09a_webui.chained_tl 同法）。"""
    rows, prev = [], core.GENESIS
    for ts, actor, phase, event in specs:
        wo = [ts, actor, phase, event, "", prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, "", prev, h, "2"])
        prev = h
    return rows


def build_goal(battle_dir, gen="G-t3"):
    """在 battle 目录下铸一个最小可服 goal（goals/budget/timeline 三表）。"""
    gd = os.path.join(battle_dir, gen)
    os.makedirs(gd, exist_ok=True)
    core.write_tsv(os.path.join(gd, "goals.tsv"), [_row(
        "goals.tsv", id=gen + "-0001", target="shop.example",
        objective="授权渗透：serve 冒烟", budget="1000;100;10",
        schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "budget.tsv"), [_row(
        "budget.tsv", timestamp=TS1, token_delta="100", requests_delta="10",
        hours_delta="0.5", scope="goal", note="P1 recon", schema_version="2")])
    core.write_tsv(os.path.join(gd, "timeline.tsv"), _chained_tl([
        (TS1, "总控", "P0", "gate-exit:P0 asserts=3 result=PASS"),
        (TS2, "总控", "P1", "add-fact " + gen + "-0001")]))
    return gd


def http_status(port, path="/favicon.ico", timeout=2):
    """探活: 返回 HTTP 状态码; 连不上返回 None。"""
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
        conn.request("GET", path)
        st = conn.getresponse().status
        resp = conn.getresponse()
        resp.read()
        conn.close()
        return st
    except OSError:
        return None


def port_refused(port, wait_s=3.0):
    """端口在 wait_s 内变为拒连（服务真停了）。"""
    deadline = time.time() + wait_s
    while time.time() < deadline:
        s = socket.socket()
        s.settimeout(0.5)
        try:
            s.connect(("127.0.0.1", port))
            s.close()
            time.sleep(0.1)
        except OSError:
            return True
    return False


class ServeBase(unittest.TestCase):
    """共用: 临时 TANYIN_HOME + battles 家底 + CLI 子进程包装 + 强制收尸。"""

    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        self.battles = os.path.join(self.home.name, "battles")
        os.makedirs(self.battles)
        self.gd = build_goal(os.path.join(self.battles, "battle-1"))

    def env(self):
        return dict(os.environ, TANYIN_HOME=self.home.name)

    def serve(self, *args, timeout=90):
        return subprocess.run(
            [sys.executable, SERVE] + list(args), capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            env=self.env(), timeout=timeout)

    def force_cleanup(self):
        """测试收尾兜底: stop 一轮 + 状态文件里的 pid 直接补刀（防半死残留）。"""
        try:
            self.serve("stop", "--json", timeout=30)
        except Exception:
            pass
        sp = os.path.join(self.home.name, "serve", "serve.json")
        try:
            with open(sp, encoding="utf-8") as f:
                pid = int(json.load(f)["pid"])
            os.kill(pid, 9)
        except Exception:
            pass


class TestServeSmoke(ServeBase):
    """冒烟: 一条命令起（自动选口/静默后台/日志落位）→ 探活 → 停 → 端口归还。"""

    def test_start_stop_roundtrip(self):
        self.addCleanup(self.force_cleanup)
        port = free_port()
        r = self.serve("start", "--ledger-dir", self.gd,
                       "--port", str(port), "--json")
        self.assertEqual(r.returncode, 0, "start rc0: %s %s" % (r.stdout, r.stderr))
        payload = json.loads(r.stdout)                    # --json 直读不炸
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["port"], port)
        self.assertEqual(payload["url"], "http://127.0.0.1:%d/" % port)
        self.assertGreater(payload["pid"], 0)
        # 探活: 未登录开放面 favicon=204（服务真在应答，不只是进程在）
        self.assertEqual(http_status(port), 204)
        # status 如实报 running
        rs = self.serve("status", "--json")
        self.assertEqual(rs.returncode, 0)
        self.assertEqual(json.loads(rs.stdout)["state"], "running")
        # stop rc0 + 端口归还 + 状态翻 not-running
        rt = self.serve("stop", "--json")
        self.assertEqual(rt.returncode, 0, rt.stderr)
        self.assertTrue(port_refused(port), "停后端口应拒连")
        rs2 = self.serve("status", "--json")
        self.assertEqual(rs2.returncode, 1)
        self.assertEqual(json.loads(rs2.stdout)["state"], "not-running")

    def test_start_default_ledger_picks_latest_battle(self):
        """缺省 ledger-dir=最新战（battle-2/G-b 而非 battle-1/G-a）——clone 即用。"""
        self.addCleanup(self.force_cleanup)
        time.sleep(0.05)                                   # 保证 mtime 后建者更新
        gd2 = build_goal(os.path.join(self.battles, "battle-2"), gen="G-t3b")
        port = free_port()
        r = self.serve("start", "--port", str(port), "--json")
        self.assertEqual(r.returncode, 0, "%s %s" % (r.stdout, r.stderr))
        payload = json.loads(r.stdout)
        self.assertEqual(payload["ledger_dir"], gd2)
        self.assertEqual(http_status(port, "/login"), 200)

    def test_start_log_lands_in_state_dir(self):
        """日志落位: $TANYIN_HOME/serve/serve.log（静默后台的输出去处，/tmp 禁令#34）。"""
        self.addCleanup(self.force_cleanup)
        port = free_port()
        r = self.serve("start", "--ledger-dir", self.gd,
                       "--port", str(port), "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)
        log = os.path.join(self.home.name, "serve", "serve.log")
        self.assertEqual(payload["log"], log)
        self.assertTrue(os.path.isfile(log), "日志文件须落位")
        with open(log, encoding="utf-8", errors="replace") as f:
            body = f.read()
        self.assertIn("方向盘", body, "webui 启动横幅应进日志: %r" % body[:200])

    def test_start_without_any_battle_rc2_guidance(self):
        """无战可服且未给 --ledger-dir=环境域 rc2（附人话指路），不是静默也不是 1。"""
        empty = tempfile.TemporaryDirectory()
        self.addCleanup(empty.cleanup)
        r = subprocess.run(
            [sys.executable, SERVE, "start", "--port", str(free_port()), "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=dict(os.environ, TANYIN_HOME=empty.name), timeout=60)
        self.assertEqual(r.returncode, 2)
        payload = json.loads(r.stdout)                    # 错误也是纯 JSON
        self.assertFalse(payload["ok"])
        self.assertIn("ledger", payload["reason"])

    def test_help_rc0_mentions_default_port(self):
        r = self.serve("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("8900", r.stdout, "--help 须披露缺省口 8900（产品形态钉）")


class TestPortConflict(ServeBase):
    """端口冲突降级: 忙则自动改口（不炸不静默），区间全忙=环境域 rc2。"""

    def test_port_busy_auto_bumps_to_next_free(self):
        self.addCleanup(self.force_cleanup)
        want = free_port()
        holder = socket.socket()
        holder.bind(("127.0.0.1", want))
        holder.listen(1)
        self.addCleanup(holder.close)
        r = self.serve("start", "--ledger-dir", self.gd,
                       "--port", str(want), "--json")
        self.assertEqual(r.returncode, 0, "冲突应降级改口而非失败: %s" % r.stderr)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["requested_port"], want, "须如实报请求口")
        self.assertEqual(payload["port"], want + 1, "紧邻下一空闲口")
        self.assertNotEqual(payload["port"], want)
        self.assertEqual(http_status(payload["port"]), 204)

    def test_port_range_exhausted_rc2(self):
        """扫满 20 个口全忙=环境域 rc2（有界扫描，不无限漂移）。"""
        base = free_port()
        holders = []
        want = base
        for _ in range(200):                              # 找 22 个连续空闲口
            try:
                s = socket.socket()
                s.bind(("127.0.0.1", want + len(holders)))
                s.listen(1)
                holders.append(s)
                if len(holders) >= 22:
                    break
            except OSError:
                want = free_port()
                for h in holders:
                    h.close()
                holders = []
        self.addCleanup(lambda: [h.close() for h in holders])
        r = self.serve("start", "--ledger-dir", self.gd,
                       "--port", str(want), "--json")
        self.assertEqual(r.returncode, 2)
        payload = json.loads(r.stdout)
        self.assertFalse(payload["ok"])


class TestJsonPurity(ServeBase):
    """--json 纯净性钉（test_ui_craft 的 CLI 版对称件）。

    test_ui_craft 钉「页面 CSS 无裸色值/杂间距」; 这里钉「stdout 无装饰行」——
    json 解析器直读整个 stdout 不炸, 对称地把杂质挡在 CI 外。
    """

    def test_start_json_stdout_parses_directly(self):
        self.addCleanup(self.force_cleanup)
        r = self.serve("start", "--ledger-dir", self.gd,
                       "--port", str(free_port()), "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)                    # 整读直解: 装饰行=炸
        for key in ("ok", "action", "state", "url", "port", "requested_port",
                    "pid", "host", "ledger_dir", "log"):
            self.assertIn(key, payload, "start JSON 缺 %s" % key)

    def test_status_and_stop_json_pure(self):
        self.addCleanup(self.force_cleanup)
        port = free_port()
        self.assertEqual(self.serve("start", "--ledger-dir", self.gd,
                                    "--port", str(port)).returncode, 0)
        rs = self.serve("status", "--json")
        self.assertEqual(rs.returncode, 0)
        sp = json.loads(rs.stdout)
        self.assertEqual(sp["action"], "status")
        rt = self.serve("stop", "--json")
        self.assertEqual(rt.returncode, 0)
        tp = json.loads(rt.stdout)
        self.assertEqual(tp["action"], "stop")
        self.assertEqual(tp["state"], "stopped")

    def test_json_mode_errors_are_json_too(self):
        """--json 下连用法错也出纯 JSON（机器可读是全通道契约，不只成功路径）。"""
        r = self.serve("frobnicate", "--json")
        self.assertEqual(r.returncode, 2)
        payload = json.loads(r.stdout)
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["reason"])

    def test_human_mode_shows_url(self):
        """无 --json=给人看的行（url 可见）；与本旗标形成对照钉。"""
        self.addCleanup(self.force_cleanup)
        port = free_port()
        r = self.serve("start", "--ledger-dir", self.gd, "--port", str(port))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("http://127.0.0.1:%d/" % port, r.stdout)


class TestExitMatrix(ServeBase):
    """退出码矩阵（与 W2b 单源退出码对齐: rc1 拒 / rc2 用法·环境·gate-error / rc3 黄灯）。"""

    def test_unknown_subcommand_rc2_usage_on_stderr(self):
        r = self.serve("frobnicate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("用法", r.stderr, "用法错落 stderr 且中文指路: %r" % r.stderr)

    def test_unknown_flag_rc2(self):
        r = self.serve("start", "--frobnicate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("未知旗标", r.stderr)

    def test_missing_ledger_dir_rc2(self):
        r = self.serve("start", "--ledger-dir",
                       os.path.join(self.home.name, "no-such-dir"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("环境", r.stderr)

    def test_start_twice_reject_rc1_already_running(self):
        """单实例模型: 已在跑=REJECT rc1（对齐 CTRL_ACTIONS launch「已在跑=拒」先例）。"""
        self.addCleanup(self.force_cleanup)
        port = free_port()
        r1 = self.serve("start", "--ledger-dir", self.gd,
                        "--port", str(port), "--json")
        self.assertEqual(r1.returncode, 0, r1.stderr)
        first = json.loads(r1.stdout)
        r2 = self.serve("start", "--ledger-dir", self.gd,
                        "--port", str(port), "--json")
        self.assertEqual(r2.returncode, 1, "二次 start 须拒: %s" % r2.stdout)
        second = json.loads(r2.stdout)
        self.assertFalse(second["ok"])
        self.assertEqual(second["reason"], "already-running")
        self.assertEqual(second["pid"], first["pid"], "拒单须指认在跑实例")

    def test_stop_not_running_rc1(self):
        r = self.serve("stop", "--json")
        self.assertEqual(r.returncode, 1)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["state"], "not-running")

    def test_status_not_running_rc1(self):
        r = self.serve("status", "--json")
        self.assertEqual(r.returncode, 1)
        payload = json.loads(r.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["state"], "not-running")

    def _write_state(self, pid, port):
        sd = os.path.join(self.home.name, "serve")
        os.makedirs(sd, exist_ok=True)
        with open(os.path.join(sd, "serve.json"), "w",
                  encoding="utf-8", newline="\n") as f:
            json.dump({"pid": pid, "port": port, "host": "127.0.0.1",
                       "url": "http://127.0.0.1:%d/" % port,
                       "ledger_dir": self.gd, "log": os.path.join(sd, "serve.log"),
                       "started": "2026-10-18T00:00:00Z"}, f)

    def test_status_stale_rc3(self):
        """黄灯①: 状态文件在而进程亡——不静默绿（W2b rc3 语义）。"""
        p = subprocess.Popen([sys.executable, "-c", "pass"])
        p.wait()                                          # pid 必死
        self._write_state(p.pid, free_port())
        r = self.serve("status", "--json")
        self.assertEqual(r.returncode, 3)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["state"], "stale")

    def test_status_degraded_rc3(self):
        """黄灯②: 进程在而端点不应答——不静默绿。"""
        sleeper = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(120)"])
        self.addCleanup(sleeper.kill)
        self._write_state(sleeper.pid, free_port())
        r = self.serve("status", "--json")
        self.assertEqual(r.returncode, 3)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["state"], "degraded")

    def test_gate_error_prefix_on_unexpected_exception(self):
        """gate-error: 未预期异常=rc2+独立事件词（bug 永不伪装 1——W2b P0-3 语义）。"""
        loader = importlib.machinery.SourceFileLoader(
            "tanyin_serve_under_test", SERVE)
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with mock.patch.object(mod, "_port_free",
                               side_effect=TypeError("boom")), \
                redirect_stdout(buf_out), redirect_stderr(buf_err), \
                mock.patch.dict(os.environ, {"TANYIN_HOME": self.home.name}):
            rc = mod.main(["tanyin-serve", "start",
                           "--ledger-dir", self.gd, "--json"])
        self.assertEqual(rc, 2)
        self.assertIn("gate-error:", buf_err.getvalue(),
                      "未预期异常须带事件词: %r" % buf_err.getvalue())


class TestRegistration(unittest.TestCase):
    """新命令面随行入册（selfcheck KNOWN_COMMANDS 冻结口径——防忘登红线）。"""

    def test_known_commands_has_serve_face(self):
        from ledger import selfcheck
        self.assertEqual(selfcheck.KNOWN_COMMANDS.get("serve"),
                         ["start", "status", "stop"])


if __name__ == "__main__":
    unittest.main()
