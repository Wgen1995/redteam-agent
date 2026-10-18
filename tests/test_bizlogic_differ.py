# -*- coding: utf-8 -*-
"""功能6 TDD②: 差分探测器(cli/bizlogic/differ.py)——先失败测试。

设计: docs/design/2026-10-20-bizlogic-layer-design.md §2。
纪律:
- RT-0006 诚实律: 零差分=无信号,如实 verdict=no-signal 不脑补候选;
- RT-0006 预算警戒: 组合数超 pair_cap → 拒收(可显式覆盖),不静默全喷
  (matrix 128 行只 15x 的学费);
- RT-0006 方法族: 模板 method 显式,默认 GET 直取——POST 脑补是陷阱;
- norm 单源: body_hash 走 ledger/norm.normalize_artifact(nonce/ts 归一已冻结);
- 执行后端注入: 本模块零 HTTP 栈,生产装配=CurlSender(tools.gate curl 卡)。
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))

from bizlogic import differ  # noqa: E402


def _resp(status=200, body="", headers=None):
    return differ.Response(status=status, body=body,
                           headers={k.lower(): v for k, v in (headers or {}).items()})


def _ids(*specs):
    """最小身份形: (label, secret_ref[, auth_context])。"""
    out = []
    for s in specs:
        out.append({"label": s[0], "secret_ref": s[1],
                    "auth_context": s[2] if len(s) > 2 else ""})
    return out


class FakeSender(object):
    def __init__(self, router=None, default=None):
        self.router = router or {}   # (identity, state) -> Response|Exception
        self.default = default
        self.calls = []

    def __call__(self, request):
        self.calls.append(request)
        v = self.router.get((request["identity"], request["state"]), self.default)
        if isinstance(v, Exception):
            raise v
        return v if v is not None else _resp()


TEMPLATE = {"method": "GET",
            "url": "https://shop.example/orders/9001?phase={state}",
            "headers": {"X-Auth-Token": "{identity}"},
            "body": ""}


class TestFingerprint(unittest.TestCase):
    def test_four_axes_present(self):
        fp = differ.fingerprint(_resp(status=403, body="no",
                                      headers={"Content-Type": "text/plain"}))
        self.assertEqual(sorted(fp), sorted(differ.AXES))
        self.assertEqual(fp["status"], 403)
        self.assertEqual(fp["length"], 2)

    def test_body_hash_norm_single_source(self):
        """同构响应仅差时间戳 → norm 后同哈希(ledger/norm 单源)。"""
        a = differ.fingerprint(_resp(body='{"ts":"2026-10-20T10:00:00Z","ok":1}'))
        b = differ.fingerprint(_resp(body='{"ts":"2026-10-20T11:00:00Z","ok":1}'))
        self.assertEqual(a["body_hash"], b["body_hash"])

    def test_key_headers_projected(self):
        fp = differ.fingerprint(_resp(headers={"X-Auth-Token": "t", "X-Ignored": "x"}),
                                key_headers=("x-auth-token",))
        self.assertEqual(fp["headers"], {"x-auth-token": "t"})
        self.assertEqual(differ.fingerprint(_resp(headers={"X-Ignored": "x"}),
                                            key_headers=("x-auth-token",))["headers"],
                         {"x-auth-token": ""}, "缺席=空串(在场/缺席差分可见)")


class TestRender(unittest.TestCase):
    def test_identity_and_state_substituted(self):
        req = differ.render(TEMPLATE, {"label": "alice", "secret_ref": "{{vault:cred-4}}"},
                            {"name": "after"})
        self.assertIn("phase=after", req["url"])
        self.assertEqual(req["headers"]["X-Auth-Token"], "{{vault:cred-4}}")
        self.assertEqual(req["method"], "GET")

    def test_anonymous_drops_empty_header(self):
        req = differ.render(TEMPLATE, {"label": "anonymous", "secret_ref": ""},
                            {"name": "before"})
        self.assertNotIn("X-Auth-Token", req["headers"], "匿名=凭据头整头删除")

    def test_method_default_get(self):
        req = differ.render({"method": "", "url": "https://t.example/a?x={state}",
                             "headers": {}, "body": ""},
                            {"label": "anonymous", "secret_ref": ""}, {"name": "s"})
        self.assertEqual(req["method"], "GET", "方法族: 缺省 GET 直取不脑补 POST")


class TestProbe(unittest.TestCase):
    def _run(self, router, ids=None, states=("before", "after"), **kw):
        ids = ids if ids is not None else _ids(("anonymous", ""),
                                               ("alice", "{{vault:cred-4}}", "CRED-x-0004"))
        sender = FakeSender(router)
        return differ.probe(TEMPLATE, ids, list(states), sender, **kw), sender

    def test_identity_signal_on_status(self):
        rep, sender = self._run({("anonymous", s): _resp(status=403, body="no")
                                 for s in ("before", "after")} |
                                {("alice", s): _resp(status=200, body="orders")
                                 for s in ("before", "after")})
        self.assertEqual(rep["verdict"], "signal")
        axes = {d["axis"] for d in rep["signals"]}
        self.assertIn("status", axes)
        self.assertEqual(rep["combo_count"], 4)
        self.assertEqual(len(sender.calls), 4, "4 组合恰 4 发")

    def test_zero_diff_honest_no_signal(self):
        rep, _ = self._run({(l, s): _resp(status=200, body="same")
                            for l in ("anonymous", "alice")
                            for s in ("before", "after")})
        self.assertEqual(rep["verdict"], "no-signal")
        self.assertEqual(rep["signals"], [])
        self.assertTrue(any("无信号" in n for n in rep["notes"]),
                        "零差分=诚实记无信号(RT-0006),不脑补")

    def test_dynamic_only_length_diff_is_noise(self):
        """norm 哈希同/状态同/头同,仅长度差(动态字段)=噪声不计信号。"""
        rep, _ = self._run({("anonymous", "before"): _resp(body="nonce=1"),
                            ("anonymous", "after"): _resp(body="nonce=1"),
                            ("alice", "before"): _resp(body="nonce=1234567"),
                            ("alice", "after"): _resp(body="nonce=1234567")})
        self.assertEqual(rep["verdict"], "no-signal")
        self.assertTrue(all(d["class"] == "noise" for d in rep["diffs"]),
                        "纯动态字段长度差=噪声")

    def test_state_axis_diff_is_signal(self):
        """同身份跨状态响应差(取消后仍 200=行为面变化)→ 状态轴信号。"""
        rep, _ = self._run({("anonymous", "before"): _resp(status=403),
                            ("anonymous", "after"): _resp(status=403),
                            ("alice", "before"): _resp(status=403, body="closed"),
                            ("alice", "after"): _resp(status=200, body="shipped")})
        state_signals = [d for d in rep["signals"] if d["scope"] == "state"]
        self.assertTrue(state_signals, "状态轴差分入信号")

    def test_cell_carries_auth_context_for_ledger(self):
        rep, _ = self._run({(l, s): _resp(status=200, body="same")
                            for l in ("anonymous", "alice")
                            for s in ("before", "after")})
        alice_cells = [c for c in rep["cells"] if c["identity"] == "alice"]
        self.assertTrue(all(c["auth_context"] == "CRED-x-0004" for c in alice_cells),
                        "格携带 auth_context=挂链纪律(RT-0016)下游直用")

    def test_sender_error_recorded_honestly(self):
        rep, _ = self._run({("anonymous", "before"): RuntimeError("guard 拒"),
                            ("anonymous", "after"): _resp(status=200),
                            ("alice", "before"): _resp(status=200),
                            ("alice", "after"): _resp(status=200)})
        self.assertTrue(any(c["error"] for c in rep["cells"]))
        self.assertIn("error_cells=1", " ".join(rep["notes"]))

    def test_all_errors_verdict_errors(self):
        rep, _ = self._run({(l, s): RuntimeError("down") for l in ("anonymous", "alice")
                            for s in ("before", "after")})
        self.assertEqual(rep["verdict"], "errors")

    def test_repeats_detect_unstable(self):
        class Flip(object):
            def __init__(self):
                self.n = 0

            def __call__(self, request):
                self.n += 1
                return _resp(status=200 if self.n % 2 else 201)

        flip = Flip()
        rep = differ.probe(TEMPLATE, _ids(("anonymous", ""), ("alice", "v")),
                           ["before"], flip, repeats=2)
        self.assertTrue(all(c["unstable"] for c in rep["cells"]), "两次不同=unstable")
        self.assertTrue(any("unstable" in n for n in rep["notes"]))


class TestBudgetGuard(unittest.TestCase):
    def test_combo_over_cap_rejected(self):
        ids = _ids(*[("u%d" % i, "s%d" % i) for i in range(5)])
        states = ["s%d" % i for i in range(6)]
        with self.assertRaises(differ.DiffBudgetError) as cm:
            differ.probe(TEMPLATE, ids, states, FakeSender(), pair_cap=24)
        self.assertIn("30", str(cm.exception), "组合数入报错信息(矩阵预算警戒)")

    def test_override_proceeds_with_warning(self):
        ids = _ids(*[("u%d" % i, "s%d" % i) for i in range(5)])
        states = ["s%d" % i for i in range(6)]
        rep = differ.probe(TEMPLATE, ids, states, FakeSender(default=_resp()),
                           pair_cap=24, override_budget=True)
        self.assertEqual(rep["combo_count"], 30)
        self.assertTrue(rep.get("budget_overridden"), "覆盖留痕")


class TestCurlArgv(unittest.TestCase):
    def test_get_argv_shape(self):
        req = {"method": "GET", "url": "https://t.example/a",
               "headers": {"X-Auth-Token": "v"}, "body": ""}
        argv = differ.curl_argv(req)
        self.assertEqual(argv[-1], "https://t.example/a", "URL 居末(CLI 卡目标位惯例)")
        self.assertIn("-X", argv)
        i = argv.index("-H")
        self.assertEqual(argv[i + 1], "X-Auth-Token: v")
        self.assertNotIn("--data-raw", argv)

    def test_post_body_and_max_time(self):
        req = {"method": "POST", "url": "https://t.example/b",
               "headers": {}, "body": "x=1"}
        argv = differ.curl_argv(req, max_time=5)
        self.assertIn("--data-raw", argv)
        self.assertIn("5", argv)


class TestCurlSender(unittest.TestCase):
    def test_parses_dump_headers_and_body(self):
        out = ("HTTP/1.1 403 Forbidden\r\nContent-Type: application/json\r\n"
               "X-Auth-Token: t\r\n\r\n{\"e\":\"no\"}")
        status, headers, body = differ.parse_curl_out(out)
        self.assertEqual(status, 403)
        self.assertEqual(headers["x-auth-token"], "t")
        self.assertEqual(body, '{"e":"no"}')

    def test_sender_routes_through_injected_backend(self):
        seen = {}

        def exec_fn(goal_dir, name, args, ts):
            seen["name"] = name
            seen["args"] = args
            seen["ts"] = ts
            return 0, "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nok", ""

        sender = differ.CurlSender("/tmp/gd", exec_fn=exec_fn, ts="2026-10-20T00:00:00Z")
        resp = sender({"method": "GET", "url": "https://t.example/a",
                      "headers": {}, "body": ""})
        self.assertEqual(resp.status, 200)
        self.assertEqual(seen["name"], "curl", "走既有 curl 卡(不另造 HTTP 栈)")
        self.assertEqual(seen["args"][-1], "https://t.example/a")
        self.assertEqual(seen["ts"], "2026-10-20T00:00:00Z")

    def test_sender_nonzero_rc_raises_sender_error(self):
        def exec_fn(*a, **k):
            return 1, "", "tools-reject: card-not-installed"

        sender = differ.CurlSender("/tmp/gd", exec_fn=exec_fn)
        with self.assertRaises(differ.SenderError):
            sender({"method": "GET", "url": "https://t.example/a",
                   "headers": {}, "body": ""})


if __name__ == "__main__":
    unittest.main()
