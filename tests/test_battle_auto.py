# -*- coding: utf-8 -*-
"""W1-T4 · battle.py auto 子命令——假战士全链 SIM（零 LLM 依赖）。

契约（任务 W1-T4）：auto = init(建战+授权校验) → launch → 看护(活性/预算/
断连救场) → 自动 settle(收敛四条件) → 自动 report；人工点只留审批卡与
P5.5 签发（auto 永不代批/代签——P5.5 signoff 留人工，见 A 例断言）。

假战士=PATH 注入的 opencode 替身（tests 内嵌脚本，无 LLM）：
  - 全链模式：经 13 表真命令打一场迷你战（intent/asset/fact+消费边/
    evidence/finding/cred/matrix-init+freeze+置格/budget-log）至 converge；
  - SIM-MODE-NOOP：立即退出（喂 runner 重启耗尽→看护 giveup）；
  - SIM-MODE-SLEEP：静默长睡（喂 idle 断连→auto-rescue 救场）。

断言各阶段账本事件齐全（actor=battle, phase=P-lifecycle 的 auto-* 事件轨）
+ 退出码：0=全链 / 1=看护 giveup 或 report 环境缺 / 2=授权校验拒或链断。

python3 -m unittest tests.test_battle_auto
"""
import datetime
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
BATTLE = os.path.join(ROOT, "scripts", "battle.py")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")

N = 901                       # 场景钟战号（2026-09-27 + 901d，避真实战号段）
GEN = "G-sim"
TS_APPROVE = "2026-10-18T08:00:00Z"

# ---- 假战士脚本（opencode 替身；由 tanyin-runner 以 cwd=ROOT 调起） ----
WARRIOR = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SIM 假战士（W1-T4 测试件）：opencode 替身，零 LLM。

调用形（tanyin-runner launch）：opencode run <任务书全文>
行为由 goal 目录标记选择：SIM-MODE-NOOP=立即退；SIM-MODE-SLEEP=静默睡；
默认=打迷你战至收敛四条件满足。幂等：SIM-WARRIOR-DONE 在场即退。
"""
import datetime
import os
import re
import subprocess
import sys
import time

LEDGER = os.path.join(os.getcwd(), "cli", "tanyin-ledger")

mission = sys.argv[2] if len(sys.argv) > 2 else ""
GD = re.search(r"会话目录：(\S+?)（", mission).group(1)
TS0 = re.search(r"场景钟=(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", mission).group(1)
_T0 = datetime.datetime.strptime(TS0, "%Y-%m-%dT%H:%M:%SZ")


def T(k):
    return (_T0 + datetime.timedelta(minutes=k)).strftime("%Y-%m-%dT%H:%M:%SZ")


def out_id(r):
    for ln in (r.stdout or "").splitlines():
        p = ln.split("\t")
        if len(p) >= 2 and p[0] == "OK":
            return p[1]
    sys.stderr.write("sim-warrior no-id: " + (r.stdout or r.stderr or "")[:300] + "\n")
    sys.exit(3)


def L(*a):
    r = subprocess.run([sys.executable, LEDGER, a[0], "--goal-dir", GD] + list(a[1:]),
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write("sim-warrior FAIL %s: %s\n" % (a[0], (r.stdout or r.stderr or "")[:300]))
        sys.exit(3)
    print("[sim-warrior] %s ok" % a[0])
    sys.stdout.flush()
    return r


if os.path.exists(os.path.join(GD, "SIM-WARRIOR-DONE")):
    print("[sim-warrior] done-marker hit, exit")
    sys.exit(0)
if os.path.exists(os.path.join(GD, "SIM-MODE-NOOP")):
    print("[sim-warrior] noop exit")
    sys.exit(0)
if os.path.exists(os.path.join(GD, "SIM-MODE-SLEEP")):
    print("[sim-warrior] sleep (silent)")
    sys.stdout.flush()
    time.sleep(600)
    sys.exit(0)

# 断点续跑（runner 重启/断连救场后重入零重复落账）：进度存 SIM-STATE.json
import json
STATE = os.path.join(GD, "SIM-STATE.json")
st = {}
if os.path.exists(STATE):
    with open(STATE, encoding="utf-8") as f:
        st = json.load(f)


def save():
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(st, f)


def step(key, fn):
    """幂等步：done 则跳过；fn 返回 id 则存档复用（重启后引用不漂移）。"""
    if key in st:
        print("[sim-warrior] skip %s (= %s)" % (key, st[key]))
        return st[key]
    rid = fn()
    st[key] = rid if rid else "done"
    save()
    return st[key]


# P0 授权门：creds 落账后过门（matrix-init 铸 P1 相位标，跳门检测要求先有 gate-exit:P0）
def _cred():
    return out_id(L("add-cred", "--kind=static-cred", "--role=user",
                    "--username-ref=sim-user", "--secret-ref={{vault:cred-1}}",
                    "--timestamp=" + T(1)))


def _p0():
    PHASES = os.path.join(os.getcwd(), "cli", "tanyin-phases")
    g = subprocess.run([sys.executable, PHASES, "gate", "--goal-dir", GD,
                        "--phase=P0", "--timestamp=" + T(1)],
                       capture_output=True, text=True)
    if g.returncode != 0:
        sys.stderr.write("sim-warrior P0 gate FAIL: " + (g.stdout or g.stderr)[:300] + "\n")
        sys.exit(3)
    print("[sim-warrior] gate P0 ok")


def _budget():
    return L("budget-log", "--token-delta=12345", "--requests-delta=42",
             "--hours-delta=0.05", "--scope=goal", "--note=SIM 战耗",
             "--timestamp=" + T(1)) and None


step("cred", _cred)
step("budget", _budget)   # v0.6 H1 红线：过门前账本须已有 budget 使用行
step("p0", _p0)
# P1 侦察 + P2 基线 + P3 置格至收敛四条件满足
iid = step("intent", lambda: out_id(L(
    "add-intent", "--title=SIM 侦察意图", "--engine=sim", "--kind=recon",
    "--origin=entity", "--budget-share=200000;5000;4", "--timestamp=" + T(2))))
ast = step("asset", lambda: out_id(L(
    "add-asset", "--type=service", "--value=sim-svc.range.local", "--timestamp=" + T(2))))
fid = step("fact", lambda: out_id(L(
    "add-fact", "--intent-id=" + iid, "--kind=service", "--target=sim-svc.range.local",
    "--detail=SIM 服务端口存活", "--confidence=0.9", "--timestamp=" + T(3))))
step("consume", lambda: L(
    "add-edge", "--kind=derived_from", "--source-id=" + fid, "--target-id=" + iid,
    "--provenance=SIM 假设消费", "--timestamp=" + T(3)) and None)
ev = step("evidence", lambda: out_id(L(
    "add-evidence", "--title=SIM 首页证据", "--source-type=manual",
    "--observed-at=" + T(4), "--network-position=internet",
    "--repro-command=curl -s http://sim-svc.range.local/",
    "--repro-kind=single", "--artifact=sim/evidence-sim.txt",
    "--raw-excerpt=SIM HTTP 200 excerpt", "--timestamp=" + T(4))))
step("finding", lambda: out_id(L(
    "add-finding", "--intent-id=" + iid, "--title=SIM 服务信息暴露",
    "--confidence=C3", "--impact=低", "--exploitation-status=suspected",
    "--scope-check=in_scope", "--description-brief=SIM 战发现（假战士铸）",
    "--reproducible-steps=curl -s http://sim-svc.range.local/",
    "--affected-asset-id=" + ast, "--evidence-ids=" + ev, "--timestamp=" + T(5))))
step("matrix-init", lambda: L("matrix-init", "--timestamp=" + T(6)) and None)
step("matrix-freeze", lambda: L("matrix-freeze", "--timestamp=" + T(6)) and None)


def _fill_gaps():
    r = L("matrix-gaps")
    k = 7
    for ln in (r.stdout or "").splitlines():
        if ln.startswith("#"):
            continue
        parts = ln.split("\t")
        if len(parts) >= 2 and parts[0].strip():
            L("matrix-set", "--attack-surface=" + parts[0], "--vuln-class=" + parts[1],
              "--state=x", "--reason=SIM 全测置格", "--timestamp=" + T(k))
            k += 1
    return None


step("fill", _fill_gaps)
with open(os.path.join(GD, "SIM-WARRIOR-DONE"), "w", encoding="utf-8") as f:
    f.write("done\n")
print("[sim-warrior] battle complete")
sys.exit(0)
'''


class AutoBase(unittest.TestCase):
    """SIM 战场脚手架：TANYIN_HOME/假 opencode/授权书/清理残兵。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="battle-auto-")
        self.home = os.path.join(self.tmp, "home")          # TANYIN_HOME
        self.battle_home = os.path.join(self.tmp, "battle-%d" % N)
        self.gd = os.path.join(self.battle_home, GEN)
        self.bindir = os.path.join(self.tmp, "bin")
        os.makedirs(self.home)
        os.makedirs(self.bindir)
        self.auth = os.path.join(self.tmp, "AUTH-SIM.pdf")
        with open(self.auth, "wb") as f:
            f.write(b"SIM authorization letter for battle-auto tests\n" * 4)
        fake = os.path.join(self.bindir, "opencode")
        with open(fake, "w", encoding="utf-8") as f:
            f.write(WARRIOR)
        os.chmod(fake, 0o755)
        self.base_env = dict(os.environ, TANYIN_HOME=self.home,
                             PATH=self.bindir + os.pathsep + os.environ.get("PATH", ""))

    def tearDown(self):
        self._kill_leftovers()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _kill_leftovers(self):
        """收割残兵：runner.pid 文件 + runner tsv 里 LAUNCH/RESTART 的 pid。"""
        pids = set()
        for dirpath, _dirs, files in os.walk(self.tmp):
            for fn in files:
                p = os.path.join(dirpath, fn)
                if fn == "runner.pid":
                    try:
                        with open(p, encoding="utf-8") as f:
                            pids.add(int(f.read().strip()))
                    except (OSError, ValueError):
                        pass
                elif fn.endswith(".runner.tsv"):
                    try:
                        with open(p, encoding="utf-8", errors="replace") as f:
                            for line in f:
                                if "\tLAUNCH\t" in line or "\tRESTART\t" in line:
                                    for tok in line.replace("(", " ").split():
                                        if tok.startswith("pid="):
                                            pids.add(int(tok[4:]))
                    except (OSError, ValueError):
                        pass
        import signal
        for pid in pids:
            for sig in (signal.SIGKILL,):
                try:
                    os.kill(pid, sig)
                except OSError:
                    pass

    def _auth_sha(self):
        with open(self.auth, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def run_auto(self, timeout=150, human_approval=False, **extra):
        """跑 battle.py auto；human_approval=True 起线程扮演审批卡人工点。"""
        argv = [sys.executable, BATTLE, "auto", "--n", str(N), "--gen", GEN,
                "--goal-dir", self.gd, "--auth-file", self.auth,
                "--signer=SIM-授权官", "--tick-sec", "1"]
        for k, v in extra.items():
            argv += ["--" + k.replace("_", "-"), str(v)]
        approver = None
        if human_approval:
            approver = threading.Thread(target=self._human_approve_card, daemon=True)
            approver.start()
        try:
            r = subprocess.run(argv, capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               cwd=ROOT, env=self.base_env, timeout=timeout)
        finally:
            if approver:
                approver.join(timeout=5)
        return r

    def _human_approve_card(self):
        """人工点①：审批卡（auto 永不代批——测试扮演人跑 ledger approve）。"""
        deadline = time.time() + 60
        while time.time() < deadline:
            if os.path.isfile(os.path.join(self.gd, "goals.tsv")):
                subprocess.run(
                    [sys.executable, LEDGER, "approve", "--goal-dir", self.gd,
                     "--command-hash=" + hashlib.sha256(b"sim-approval-card").hexdigest(),
                     "--decision=approved", "--approver=SIM-人工",
                     "--note=SIM 审批卡人工点", "--timestamp=" + TS_APPROVE],
                    capture_output=True, text=True, cwd=ROOT)
                return
            time.sleep(0.5)

    # ---- 读账面 ----
    def tl_events(self):
        p = os.path.join(self.gd, "timeline.tsv")
        if not os.path.isfile(p):
            return []
        with open(p, encoding="utf-8", errors="replace") as f:
            return [ln.split("\t")[3] for ln in f if ln.count("\t") >= 3]

    def auto_events(self, prefix):
        return [e for e in self.tl_events() if e.startswith(prefix)]


class TestAutoFullChain(AutoBase):
    """A 例：全链成功——init→launch→看护→settle→report，人工点=审批卡。"""

    def test_full_chain_events_and_exit_zero(self):
        r = self.run_auto(timeout=150, human_approval=True,
                          max_hours=0.5, idle_timeout=90, max_rescues=2,
                          max_restarts=6, backoff_base=0.2,
                          stall_min=6, soft_stall_min=2)
        self.assertEqual(r.returncode, 0, "rc=%s\nSTDOUT:%s\nSTDERR:%s"
                         % (r.returncode, r.stdout[-2000:], r.stderr[-2000:]))
        ev = self.tl_events()
        # 各阶段账本事件齐全（auto-* 事件轨）且顺序不逆
        def idx(pred, what):
            hits = [i for i, e in enumerate(ev) if pred(e)]
            self.assertTrue(hits, "缺 %s 事件；timeline=%s" % (what, ev))
            return hits[0]
        i_init = idx(lambda e: e.startswith("auto-init ") and "authz=PASS" in e, "auto-init authz=PASS")
        i_launch = idx(lambda e: e.startswith("auto-launch "), "auto-launch")
        i_settle = idx(lambda e: e.startswith("auto-settle ") and "verdict=converged" in e
                       and "chain=PASS" in e, "auto-settle verdict=converged chain=PASS")
        i_report = idx(lambda e: e.startswith("auto-report ") and "ok" in e, "auto-report ok")
        self.assertLess(i_init, i_launch)
        self.assertLess(i_launch, i_settle)
        self.assertLess(i_settle, i_report)
        # 战士真打了仗（13 表面到位的非空证据——finding 与 matrix-freeze 在链）
        self.assertTrue(any(e.startswith("add-finding ") for e in ev), "假战士未铸 finding")
        self.assertTrue(any(e.startswith("matrix-freeze") for e in ev), "假战士未冻结矩阵")
        # 人工点只留审批卡与 P5.5：auto 不代签发（无 P5.5 过门事件）
        self.assertFalse(any(e.startswith("gate-exit:P5.5") for e in ev),
                          "auto 不得代人工过 P5.5 签发门")
        # 审批卡=人工落账（approver 须为测试扮演的 SIM-人工，非 battle 代批）
        ap = os.path.join(self.gd, "approvals.tsv")
        self.assertTrue(os.path.isfile(ap), "审批卡未落 approvals.tsv")
        with open(ap, encoding="utf-8") as f:
            rows = [ln.split("\t") for ln in f if ln.strip()]
        self.assertTrue(rows and all(r[3] == "SIM-人工" for r in rows),
                        "approvals 行须全部来自人工: %r" % rows)
        # settle/report 产物
        sr = os.path.join(self.battle_home, "settle-report.txt")
        self.assertTrue(os.path.isfile(sr), "缺 settle-report.txt")
        with open(sr, encoding="utf-8", errors="replace") as f:
            self.assertIn("verify-chain: PASS", f.read())
        draft = os.path.join(self.gd, "report", "draft-data.json")
        self.assertTrue(os.path.isfile(draft), "缺 report/draft-data.json")
        # 收官账本链完整
        vc = subprocess.run([sys.executable, LEDGER, "verify-chain", "--goal-dir", self.gd],
                            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(vc.returncode, 0, vc.stdout + vc.stderr)
        # 引擎真的点火过（runner 轨）
        rt = os.path.join(self.battle_home, "opencode-run.log.runner.tsv")
        self.assertTrue(os.path.isfile(rt), "缺 runner 轨")
        with open(rt, encoding="utf-8") as f:
            self.assertIn("LAUNCH", f.read(), "runner 轨无点火记录")


class TestAutoAuthzReject(AutoBase):
    """B 例：授权校验拒——窗口不覆场景钟 → rc2 + authz=FAIL + 零点火。"""

    def test_window_not_covering_scenario_clock_rejected(self):
        r = self.run_auto(timeout=60, valid_from="2020-01-01T00:00:00Z",
                          valid_until="2020-01-02T00:00:00Z")
        self.assertEqual(r.returncode, 2, "rc=%s\nOUT:%s\nERR:%s" % (r.returncode, r.stdout, r.stderr))
        fails = self.auto_events("auto-init")
        self.assertTrue(fails and "authz=FAIL" in fails[0],
                        "缺 auto-init authz=FAIL 事件: %r" % fails)
        self.assertFalse(self.auto_events("auto-launch"), "授权拒后不得点火")
        self.assertFalse(os.path.exists(os.path.join(self.battle_home, "mission.txt")),
                         "授权拒后不得下发任务书")


class TestAutoGuardGiveup(AutoBase):
    """C 例：看护 giveup——假战士 noop 即退，runner 重启耗尽亡 → rc1。"""

    def test_noop_warrior_runner_death_gives_up(self):
        os.makedirs(self.gd, exist_ok=True)
        with open(os.path.join(self.gd, "SIM-MODE-NOOP"), "w") as f:
            f.write("1")
        r = self.run_auto(timeout=90, max_hours=0.2, idle_timeout=120,
                          max_rescues=0, max_restarts=1, backoff_base=0)
        self.assertEqual(r.returncode, 1, "rc=%s\nOUT:%s\nERR:%s" % (r.returncode, r.stdout, r.stderr))
        gives = self.auto_events("auto-giveup")
        self.assertTrue(gives and "reason=runner-exit" in gives[0],
                        "缺 auto-giveup reason=runner-exit 事件: %r" % gives)
        self.assertFalse(self.auto_events("auto-settle"), "未收敛不得 settle")
        self.assertFalse(self.auto_events("auto-report"), "未收敛不得 report")


class TestAutoIdleRescue(AutoBase):
    """D 例：断连救场——假战士静默长睡，idle 断连→auto-rescue→再断→giveup。"""

    def test_idle_disconnect_rescue_then_giveup(self):
        os.makedirs(self.gd, exist_ok=True)
        with open(os.path.join(self.gd, "SIM-MODE-SLEEP"), "w") as f:
            f.write("1")
        r = self.run_auto(timeout=90, max_hours=0.2, idle_timeout=4,
                          max_rescues=1, max_restarts=8, backoff_base=0.2,
                          stall_min=6, soft_stall_min=2)
        self.assertEqual(r.returncode, 1, "rc=%s\nOUT:%s\nERR:%s" % (r.returncode, r.stdout, r.stderr))
        rescues = self.auto_events("auto-rescue")
        self.assertTrue(rescues, "缺 auto-rescue 断连救场事件")
        self.assertTrue(all("reason=idle" in e for e in rescues), "救场原因应为 idle: %r" % rescues)
        gives = self.auto_events("auto-giveup")
        self.assertTrue(gives, "救场耗尽后缺 auto-giveup 事件")
        self.assertFalse(self.auto_events("auto-settle"), "未收敛不得 settle")


class TestAutoReportEnvMissing(AutoBase):
    """E 例：无人审批卡 → approvals.tsv 缺 → report 聚合 ENV → rc1 如实报缺。"""

    def test_report_fails_without_human_approval_table(self):
        r = self.run_auto(timeout=150, human_approval=False,
                          max_hours=0.5, idle_timeout=90, max_rescues=2,
                          max_restarts=6, backoff_base=0.2,
                          stall_min=6, soft_stall_min=2)
        self.assertEqual(r.returncode, 1, "rc=%s\nOUT:%s\nERR:%s" % (r.returncode, r.stdout, r.stderr))
        self.assertTrue(self.auto_events("auto-settle"), "settle 应已完成（缺表只伤 report）")
        fails = self.auto_events("auto-report")
        self.assertTrue(fails and "fail" in fails[0], "缺 auto-report fail 事件: %r" % fails)
        self.assertFalse(os.path.isfile(os.path.join(self.gd, "approvals.tsv")),
                         "本例无人工点，approvals.tsv 不应在场")
        self.assertFalse(os.path.isfile(os.path.join(self.gd, "report", "draft-data.json")),
                         "聚合失败不得产出草稿")


if __name__ == "__main__":
    unittest.main()
