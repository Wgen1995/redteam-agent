# -*- coding: utf-8 -*-
"""B:G2（B-csai 全件对齐 G2 裁决）——tanyin-guard setrlimit 资源上限 fail-closed。

规格（docs/reviews/2026-10-18-realign/B-csai-全件对齐.md G2）:
- guard exec/inject 位统一施加 RLIMIT_AS/RLIMIT_NPROC/RLIMIT_CPU;
- 参数=goal 侧可调(amendment)——13 表列集冻结(contracts), 落位=goal 目录
  guard-limits.json 侧车(操作员单写面, 先例=engines 的 task-constraints.json);
- 施加失败=REJECT(fail-closed 同律); 平台无执法能力(Windows 无 resource/
  macOS 内核不收有限 AS 值)=披露放行, CPU/NPROC 仍帽(部署文档可选档=JobObject/cgroup);
- 缺省帽常开(POSIX): as=4G/nproc=256(对齐 CSAI processguard)/cpu=600(=guard
  --timeout 上限同律); 声明值越界/坏 json/未知键=REJECT。

红线纪律: 缺省路径时间线零新行(既有 request-ticket 行数断言不破)。
"""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import re
import resource
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, "..", "cli", "tanyin-guard")
FIX = os.path.join(HERE, "fixtures", "G-g1")
PY = sys.executable
TS = "2026-09-30T12:00:00Z"
POSIX = os.name == "posix"

# 子进程自报帽值载体: 打印 "AS=<soft>/<hard>;NPROC=..;CPU=.."
REPORT = ("import resource" + chr(10) +
          "def g(n):" + chr(10) +
          "    s, h = resource.getrlimit(getattr(resource, n))" + chr(10) +
          "    print('%s=%s/%s' % (n, s, h))" + chr(10) +
          "g('RLIMIT_AS'); g('RLIMIT_NPROC'); g('RLIMIT_CPU')")
REPORT_RE = re.compile(r"RLIMIT_(AS|NPROC|CPU)=(-?\d+|-1)/(-?\d+|-1)")


def caps_of(text):
    """自报文本 → {名: 'soft/hard'}（值组不进键）。"""
    return {m.group(1): m.group(2) + "/" + m.group(3)
            for m in REPORT_RE.finditer(text)}


def g(gd, *args):
    return subprocess.run([PY, GUARD, "exec", "--goal-dir", gd,
                           "--timestamp=" + TS] + list(args),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=120)


def load_guard_module():
    """cli/tanyin-guard 以模块形态装载（in-process 用例用）。"""
    loader = importlib.machinery.SourceFileLoader("tanyin_guard_b_g2", GUARD)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def as_supported(cap):
    """本机 RLIMIT_AS 可否收到有限值（soft-only 探针, 可逆）。"""
    res = resource.RLIMIT_AS
    orig = resource.getrlimit(res)
    try:
        resource.setrlimit(res, (cap, orig[1]))
        return True
    except (ValueError, OSError):
        return False
    finally:
        with contextlib.suppress(Exception):
            resource.setrlimit(res, orig)


class _FixtureMixin(object):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def tearDown(self):
        self.td.cleanup()

    def sidecar(self, obj, raw=None):
        p = os.path.join(self.gd, "guard-limits.json")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(raw if raw is not None else json.dumps(obj))
        return p

    def timeline(self):
        p = os.path.join(self.gd, "timeline.tsv")
        return open(p, encoding="utf-8").read()


@unittest.skipUnless(POSIX, "setrlimit 执法面=POSIX")
class GuardRlimitDefaults(_FixtureMixin, unittest.TestCase):
    def test_defaults_enforced_no_sidecar(self):
        """无侧车=缺省帽常开: 子进程自报 as=4G/nproc=256/cpu=600(soft==hard)。"""
        r = g(self.gd, "--", PY, "-c", REPORT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        caps = caps_of(r.stdout)
        if as_supported(4 << 30):
            self.assertEqual(caps.get("AS"), "%d/%d" % (4 << 30, 4 << 30))
        self.assertEqual(caps.get("NPROC"), "256/256")
        self.assertEqual(caps.get("CPU"), "600/600")

    def test_defaults_no_extra_timeline_rows(self):
        """缺省路径时间线零新行(只 request-ticket 一行)——既有断言面不破。"""
        before = len(self.timeline().splitlines())
        r = g(self.gd, "--", PY, "-c", "pass")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        after = self.timeline().splitlines()
        self.assertEqual(len(after), before + 1)
        self.assertIn("request-ticket", after[-1])


@unittest.skipUnless(POSIX, "setrlimit 执法面=POSIX")
class GuardRlimitSidecar(_FixtureMixin, unittest.TestCase):
    def test_sidecar_overrides_and_audited(self):
        """侧车值生效且 amendment 报账(guard-rlimit 行在执行前)。"""
        self.sidecar({"rlimit_cpu": 120, "rlimit_nproc": 64, "rlimit_as": "2G"})
        before = len(self.timeline().splitlines())
        r = g(self.gd, "--", PY, "-c", REPORT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        caps = caps_of(r.stdout)
        self.assertEqual(caps.get("NPROC"), "64/64")
        self.assertEqual(caps.get("CPU"), "120/120")
        if as_supported(2 << 30):
            self.assertEqual(caps.get("AS"), "%d/%d" % (2 << 30, 2 << 30))
        after = self.timeline().splitlines()
        self.assertGreaterEqual(len(after), before + 2)
        ev = "\n".join(after[before:])
        self.assertIn("guard-rlimit", ev)
        self.assertIn("cpu=120", ev)

    def test_partial_sidecar_merges_defaults(self):
        """只声明一key: 其余走缺省(声明面=覆盖, 非替换)。"""
        self.sidecar({"rlimit_cpu": 33})
        r = g(self.gd, "--", PY, "-c", REPORT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        caps = caps_of(r.stdout)
        self.assertEqual(caps.get("CPU"), "33/33")
        self.assertEqual(caps.get("NPROC"), "256/256")


@unittest.skipUnless(POSIX, "setrlimit 执法面=POSIX")
class GuardRlimitOverLimit(_FixtureMixin, unittest.TestCase):
    def test_cpu_overlimit_killed(self):
        """cpu=1 + 死循环 → SIGXCPU/SIGKILL(rc!=0)且快速收敛。"""
        self.sidecar({"rlimit_cpu": 1})
        spin = "while True: pass"
        r = g(self.gd, "--", PY, "-c", spin)
        self.assertNotEqual(r.returncode, 0)
        self.assertLess(len(r.stdout), 200)

    def test_nproc_overlimit_fork_blocked(self):
        """nproc=1 → 子进程再 fork 被拒(EAGAIN)rc!=0——fork 炸弹帽。"""
        self.sidecar({"rlimit_nproc": 1})
        bomb = ("import subprocess, sys" + chr(10) +
                "r = subprocess.run([sys.executable, '-c', 'pass'])" + chr(10) +
                "print('CHILD-RC', r.returncode)")
        r = g(self.gd, "--", PY, "-c", bomb)
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("CHILD-RC 0", r.stdout)

    @unittest.skipUnless(as_supported(256 << 20), "本机 AS 无执法能力(macOS 内核不收有限值)")
    def test_as_overlimit_memoryerror(self):
        """as=256M + 分配 512M → MemoryError rc!=0。"""
        self.sidecar({"rlimit_as": "256M"})
        alloc = "b = bytearray(512 * 1024 * 1024)"
        r = g(self.gd, "--", PY, "-c", alloc)
        self.assertNotEqual(r.returncode, 0)


class GuardRlimitFailClosed(_FixtureMixin, unittest.TestCase):
    """fail-closed 面（跨平台: 校验先于平台分支）。"""

    def _rejects(self, r, needle):
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("REJECT", r.stdout)
        self.assertIn(needle, r.stdout)
        self.assertIn("guard-reject rlimit", self.timeline())

    def test_invalid_json_rejected(self):
        self.sidecar(None, raw="{not json")
        self._rejects(g(self.gd, "--", PY, "-c", "pass"), "rlimit")

    def test_unknown_key_rejected(self):
        self.sidecar({"rlimit_fsize": 100})
        self._rejects(g(self.gd, "--", PY, "-c", "pass"), "rlimit_fsize")

    def test_out_of_bounds_rejected(self):
        for bad in ({"rlimit_cpu": 0}, {"rlimit_nproc": 999999},
                    {"rlimit_as": "8M"}, {"rlimit_as": "128G"},
                    {"rlimit_cpu": 86401}, {"rlimit_nproc": 0}):
            with self.subTest(bad=bad):
                self.sidecar(bad)
                self._rejects(g(self.gd, "--", PY, "-c", "pass"), "rlimit")

    def test_malformed_value_rejected(self):
        self.sidecar({"rlimit_as": "5X"})
        self._rejects(g(self.gd, "--", PY, "-c", "pass"), "rlimit_as")

    def test_declared_limits_on_resourceless_platform_rejected(self):
        """平台无 resource(Windows) 且声明了帽 → REJECT(声明即执法义务)。"""
        mod = load_guard_module()
        self.sidecar({"rlimit_cpu": 60})
        real = mod._resource
        mod._resource = None
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = mod.cmd_exec(self.gd, ["--timestamp=" + TS, "--",
                                            PY, "-c", "pass"])
        finally:
            mod._resource = real
        self.assertEqual(rc, 1)
        self.assertIn("REJECT", out.getvalue())

    @unittest.skipUnless(POSIX, "施加失败注入面=POSIX")
    def test_apply_failure_rejects(self):
        """施加失败(注入 setrlimit 异常)=REJECT, 子进程绝不裸跑。"""
        mod = load_guard_module()
        self.sidecar({"rlimit_cpu": 60})

        class Boom(object):
            RLIMIT_CPU = resource.RLIMIT_CPU
            RLIMIT_AS = resource.RLIMIT_AS
            RLIMIT_NPROC = resource.RLIMIT_NPROC
            RLIM_INFINITY = resource.RLIM_INFINITY

            @staticmethod
            def getrlimit(res):
                return resource.getrlimit(res)

            @staticmethod
            def setrlimit(res, val):
                raise OSError(1, "injected apply failure")

        real = mod._resource
        mod._resource = Boom
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = mod.cmd_exec(self.gd, ["--timestamp=" + TS, "--",
                                            PY, "-c", "print('RAN')"])
        finally:
            mod._resource = real
        self.assertEqual(rc, 1)
        self.assertIn("REJECT", out.getvalue())
        self.assertIn("apply", out.getvalue().lower())
        self.assertNotIn("RAN", out.getvalue(), "施加失败子进程不得执行")
        self.assertIn("guard-reject rlimit", self.timeline())


@unittest.skipUnless(POSIX, "inject 执法面=POSIX")
class GuardRlimitInject(_FixtureMixin, unittest.TestCase):
    def test_inject_child_limited(self):
        """inject 通道同帽(凭据注入不绕资源上限)。"""
        # 夹具 G-g1 无 vault——先铺 .key（test_guard.GuardVault 同式）再铸真凭据。
        os.makedirs(os.path.join(self.gd, "vault"), exist_ok=True)
        with open(os.path.join(self.gd, "vault", ".key"), "w", encoding="utf-8", newline="\n") as f:
            f.write("k1")
        env = dict(os.environ, TANYIN_VAULT_SECRET="s3")
        subprocess.run([PY, GUARD, "deploy-vault", "--goal-dir", self.gd,
                        "--cred=7", "--username=u", "--timestamp=" + TS],
                       capture_output=True, text=True, env=env, timeout=60)
        subprocess.run([PY, os.path.join(HERE, "..", "cli", "tanyin-ledger"),
                        "add-scope", "--goal-dir", self.gd,
                        "--kind=account-grant", "--matcher=grant.example",
                        "--account=7", "--permitted-actions=probe",
                        "--timestamp=2026-09-23T09:00:00Z"],
                       capture_output=True, text=True, timeout=60)
        r = subprocess.run([PY, GUARD, "inject", "--goal-dir", self.gd,
                            "--cred=7", "--action=probe",
                            "--timestamp=" + TS, "--", PY, "-c", REPORT],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        caps = caps_of(r.stdout)
        self.assertEqual(caps.get("NPROC"), "256/256")
        self.assertEqual(caps.get("CPU"), "600/600")


if __name__ == "__main__":
    unittest.main()
