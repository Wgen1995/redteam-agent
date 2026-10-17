#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""battle.py · 全战外环 v2.1（可移植版）——22 战手工循环的代码化

变更（对 v2）：
- 数据落 ~/.tanyin/battles（持久；TANYIN_HOME 可覆盖）——不再用 /tmp
- Windows 兼容：零 POSIX 依赖（nohup/pgrep/tail/wc/start_new_session 均替换）

一条命令一整战：init → launch（引擎托管）→ watch → settle（评分+归因）。
场景钟：battle N = 2026-09-27 + N 天 09:00Z（b22=10-19 实测锚定）。
"""
import argparse
import datetime
import hashlib
import os
import signal
import subprocess
import sys
import time

IS_WIN = os.name == "nt"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
RUNNER = os.path.join(ROOT, "cli", "tanyin-runner")
REPORT = os.path.join(ROOT, "cli", "tanyin-report")   # W1-T4：auto report 聚合器
COMPOSE = os.path.join(ROOT, "tests", "range", "docker-compose.yml")
GT = os.path.join(ROOT, "tests", "range", "ground-truth.json")
EVAL = os.path.join(ROOT, "tests", "eval_range_recall.py")
TANYIN_HOME = os.environ.get("TANYIN_HOME") or os.path.join(os.path.expanduser("~"), ".tanyin")
BASE = os.path.join(TANYIN_HOME, "battles")


def gt_out_path(gen):
    """v0.5a F8：GT 出仓——评测真相存 ~/.tanyin/gt/<gen>.json（仓外，战士须主动越界才见）。"""
    return os.path.join(TANYIN_HOME, "gt", gen + ".json")


def ensure_gt(gen, src=GT):
    """init 时把仓内 GT 拷到仓外 gt 位（settle 只读仓外；拷贝失败回落仓内+WARN）。"""
    dst = gt_out_path(gen)
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        import shutil
        shutil.copyfile(src, dst)
        return dst
    except OSError:
        return src


def settle_gt(gen):
    """settle 用 GT：优先仓外 gt 位；缺失回落仓内（旧战兼容）。"""
    dst = gt_out_path(gen)
    return dst if os.path.isfile(dst) else GT


def popen_kwargs():
    if IS_WIN:
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {"start_new_session": True}


def run(argv, **kw):
    return subprocess.run(argv, capture_output=True, text=True, **kw)


def tail_lines(path, n=5):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.readlines()[-n:]
    except OSError:
        return []


def count_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def pid_alive(pid):
    try:
        if IS_WIN:
            r = run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"])
            return str(pid) in r.stdout
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def last_launch_pid(runner_tsv):
    for line in reversed(tail_lines(runner_tsv, 30)):
        if "\tLAUNCH\t" in line or "\tRESTART\t" in line:
            for tok in line.replace("(", " ").split():
                if tok.startswith("pid="):
                    try:
                        return int(tok[4:])
                    except ValueError:
                        pass
    return None


def clock(n):
    d = datetime.date(2026, 9, 27) + datetime.timedelta(days=n)
    return d.strftime("%Y-%m-%dT09:00:00Z"), d.strftime("%Y-%m-%d")


def paths(n, gen):
    home = os.path.join(BASE, "battle-%d" % n)
    return {
        "home": home, "goal": os.path.join(home, gen),
        "probe": os.path.join(home, "probe"),
        "mission": os.path.join(home, "mission.txt"),
        "log": os.path.join(home, "opencode-run.log"),
        "runner": os.path.join(home, "opencode-run.log.runner.tsv"),
        "directive": os.path.join(home, "directive.txt"),
        "ask": os.path.join(home, "ask.md"),
        "runner_out": os.path.join(home, "runner.out"),
    }


def ledger(*args):
    return run([sys.executable, LEDGER] + list(args))


WALL_ACTOR = "battle"        # 外环工具名（llmpool_wire actor=llmpool 先例）
WALL_PHASE = "P-lifecycle"   # 跨阶段基础设施事件轨（wallclock/llmpool_wire 同轨）


def _ledger_mods():
    """lazy 导 ledger（脚本形态：ROOT/cli 不在默认 sys.path）。"""
    sys.path.insert(0, os.path.join(ROOT, "cli"))
    from ledger import core, timeline, wallclock
    return core, timeline, wallclock


def mint_wall(goal_dir, phase, note=""):
    """Task WC 三铸点共用：clock-sync 墙钟事件铸入 goal 账本哈希链。

    - payload=ledger.wallclock.event_text——detect_gaps 解析的单源格式；
    - 行写=ledger.timeline.append_tl_locked 单源写方（v0.8 Task W llmpool_wire
      先例：goal 锁内读表→算链→写回，不私铸链行）。已知偏差：wallclock.
      mint_wall_sync 旧路经 phases_engine._append_event，该函数签名漂移
      （ts 必填化）后调即 TypeError，wallclock.py 不在本任务白名单——接线
      不经它；payload/检出仍复用 wallclock 模块保格式单源。
    - 行 ts=负载 wall= 值（行与负载墙钟严格同源）；actor="battle"、
      phase="P-lifecycle"、revert 空。
    - fail-open 观测轨：账本未生（agent 模式 init/launch 正常态——账本由
      战士自建）跳过；铸造失败仅 WARN 不外抛——墙钟轨不炸战斗主流程。
    """
    try:
        if not os.path.isfile(os.path.join(goal_dir, "timeline.tsv")):
            print("[wall] 账本未生，跳过 %s 铸点（agent 模式正常态）" % phase)
            return None
        _core, timeline, wallclock = _ledger_mods()
        ev = wallclock.event_text(phase, note)
        ts = ev.split("wall=")[1].split()[0]
        timeline.append_tl_locked(goal_dir, ts, ev, WALL_ACTOR, WALL_PHASE)
        print("[wall] %s" % ev)
        return ev
    except Exception as e:
        print("[wall] WARN %s 铸点失败：%r（观测轨 fail-open，主流程继续）" % (phase, e))
        return None


def wall_gaps(goal_dir, min_sec=900):
    """settle 侧断连窗口检出：timeline 行过 wallclock.detect_gaps（v0.7b 纯函数）。

    detect_gaps 吃 dict/str 行——Session.rows 返回列表行，str(list) 自带
    引号尾料会撑爆 _WALL_RE 的 $ 锚（无 note 行失配），故先抽 event 列。"""
    try:
        core, _timeline, wallclock = _ledger_mods()
        ev_i = core.TABLES["timeline.tsv"].index("event")
        return wallclock.detect_gaps(
            [r[ev_i] for r in core.Session(goal_dir).rows("timeline.tsv")], min_sec)
    except Exception as e:
        print("[wall] WARN 断连窗口读取失败：%r" % e)
        return []


# ------------------------------------- W1-T4 auto：一键全链（init→launch→看护→settle→report）

def _now_utc_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def auto_mint(goal_dir, event):
    """auto 生命周期事件入链（actor=battle / phase=P-lifecycle，墙钟轨同款；

    行写=timeline.append_tl_locked 单源写方（test_wallclock_wire 单源钉）。
    fail-open：铸造失败 WARN 不炸主流程（事件缺失由验收测试把门）。"""
    try:
        _core, timeline, _wc = _ledger_mods()
        timeline.append_tl_locked(goal_dir, _now_utc_iso(), event, WALL_ACTOR, WALL_PHASE)
        print("[auto] %s" % event)
        return True
    except Exception as e:
        print("[auto] WARN 事件铸造失败 %r（%s）" % (e, event))
        return False


def _goal_row(goal_dir):
    """goals 末行投影 dict（缺账本=None）。"""
    try:
        core, _tl, _wc = _ledger_mods()
        rows = core.Session(goal_dir).rows("goals.tsv")
        return dict(zip(core.TABLES["goals.tsv"], rows[-1])) if rows else None
    except Exception:
        return None


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def authz_check(goal_dir, ts):
    """授权校验（auto init 第二半）：五查全过才开战。

    ① goals 行在位 ② auth_sha256 形合 ③ 授权书在位且实测 sha 一致（真校验链，
    无豁免通道——W1-T1 同律）④ 窗口覆场景钟（战斗一切 --timestamp 的操作钟）
    ⑤ verify-chain PASS + scope include/exclude/oob 齐备（P0 断言同款）。
    返回 (ok, reason, goal_row)。"""
    g = _goal_row(goal_dir)
    if not g:
        return False, "no-goal-row", g
    sha = (g.get("auth_sha256") or "").lower()
    if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        return False, "auth-sha256-not-hex", g
    doc = g.get("auth_doc") or ""
    path = doc if os.path.isfile(doc) else os.path.join(goal_dir, doc)
    if not os.path.isfile(path):
        return False, "auth-doc-missing", g
    if _sha256_file(path) != sha:
        return False, "auth-sha256-mismatch", g
    vf, vu = g.get("valid_from") or "", g.get("valid_until") or ""
    if not (vf and vu and vf <= ts <= vu):
        return False, "window-not-covering-clock(%s..%s@%s)" % (vf, vu, ts), g
    try:
        core, _tl, _wc = _ledger_mods()
        kinds = {dict(zip(core.TABLES["scope.tsv"], r)).get("kind", "")
                 for r in core.Session(goal_dir).rows("scope.tsv")}
    except Exception:
        kinds = set()
    for need in ("include", "exclude", "oob"):
        if need not in kinds:
            return False, "scope-missing-kind=%s" % need, g
    vr = ledger("verify-chain", "--goal-dir", goal_dir)
    if vr.returncode != 0:
        return False, "verify-chain-fail", g
    return True, "", g


def matrix_frozen(goal_dir):
    """P2 完成的账面凭据：timeline 已有 matrix-freeze 事件。

    auto 的收敛判定只认冻结后的 converge-check——空账 trivially-converged
    （无矩阵/无事实）不是战毕，是未开打（P3 收敛语义=P2 之后的循环出口）。"""
    try:
        with open(os.path.join(goal_dir, "timeline.tsv"), encoding="utf-8",
                  errors="replace") as f:
            return any(ln.split("\t")[3].startswith("matrix-freeze")
                       for ln in f if ln.count("\t") >= 3)
    except OSError:
        return False


def converge_verdict(goal_dir):
    """converge-check 首词（converged/budget-exhausted/running/""）。"""
    r = ledger("converge-check", "--goal-dir", goal_dir)
    line = (r.stdout or "").strip().splitlines()[0] if (r.stdout or "").strip() else ""
    return line.split("（")[0].strip() if r.returncode == 0 else ""


def auto_paths(goal_dir):
    """auto 战目录布局：home=goal-dir 母目录（键名与 paths() 对齐）。"""
    goal = os.path.abspath(goal_dir)
    home = os.path.dirname(goal) or "."
    return {
        "home": home, "goal": goal,
        "probe": os.path.join(home, "probe"),
        "mission": os.path.join(home, "mission.txt"),
        "log": os.path.join(home, "opencode-run.log"),
        "runner": os.path.join(home, "opencode-run.log.runner.tsv"),
        "directive": os.path.join(home, "directive.txt"),
        "ask": os.path.join(home, "ask.md"),
        "runner_out": os.path.join(home, "runner.out"),
        "runner_pid": os.path.join(home, "runner.pid"),
    }


def auto_spawn_runner(p, a):
    """点火引擎（cmd_launch 同款参面 + tick 透传；runner.pid 落盘供救场/收割）。"""
    os.makedirs(os.path.dirname(p["directive"]), exist_ok=True)
    if not os.path.exists(p["directive"]):
        with open(p["directive"], "w", encoding="utf-8") as f:
            f.write("")   # 空指令文件：digest 基线
    argv = [sys.executable, RUNNER, "start", "--cwd", ROOT,
            "--prompt-file", p["mission"], "--log", p["log"],
            "--ledger-dir", p["goal"], "--max-restarts", str(a.max_restarts),
            "--stall-min", str(a.stall_min), "--soft-stall-min", str(a.soft_stall_min),
            "--backoff-base", str(a.backoff_base), "--tick-sec", str(a.tick_sec),
            "--directive-file", p["directive"], "--ask-file", p["ask"]]
    if getattr(a, "model", None):
        argv += ["--model", a.model]
    out = open(p["runner_out"], "a", encoding="utf-8")
    proc = subprocess.Popen(argv, stdout=out, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, cwd=ROOT,
                            env=dict(os.environ, TANYIN_ANCHOR_AUTO="1"),
                            **popen_kwargs())
    with open(p["runner_pid"], "w", encoding="utf-8") as f:
        f.write(str(proc.pid))
    return proc


def auto_kill_tree(proc, p):
    """双杀：战士 pid（runner 各自 start_new_session，pgid 够不着它）+ runner 组。"""
    wpid = last_launch_pid(p["runner"])
    if wpid:
        try:
            if IS_WIN:
                run(["taskkill", "/F", "/T", "/PID", str(wpid)])
            else:
                os.kill(wpid, signal.SIGKILL)
        except OSError:
            pass
    if proc is not None and proc.poll() is None:
        try:
            if IS_WIN:
                run(["taskkill", "/F", "/T", "/PID", str(proc.pid)])
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (OSError, PermissionError):
            try:
                proc.kill()
            except OSError:
                pass
    if proc is not None:
        try:
            proc.wait(timeout=10)
        except Exception:
            pass


def _auto_giveup(p, reason, rescues):
    auto_mint(p["goal"], "auto-giveup reason=%s rescues=%d" % (reason, rescues))
    print("[auto] 战未收敛放弃（%s，救场 %d 次）——人工接管：watch/settle 复跑或 directive 介入"
          % (reason, rescues))
    sys.exit(1)


def cmd_auto(a):
    """auto 一键全链：init(建战+授权校验)→launch→看护(活性/预算/断连救场)→
    自动 settle(收敛四条件)→自动 report。人工点只留审批卡与 P5.5 签发——
    auto 永不 approve/永不 sign（报告止步聚合草稿，签发属人工）。"""
    p = auto_paths(a.goal_dir)
    ts0, day = clock(a.n)
    os.makedirs(p["probe"], exist_ok=True)
    os.makedirs(p["goal"], exist_ok=True)
    boot = "resume" if os.path.isfile(os.path.join(p["goal"], "goals.tsv")) else "fresh"
    # ---- ① init：建战（fresh 才铸账；resume=续战复用既有账本）----
    if boot == "fresh":
        if not a.auth_file or not a.signer:
            sys.exit("auto 建战须 --auth-file 与 --signer（真授权四件，无豁免通道）")
        if not os.path.isfile(a.auth_file):
            auto_mint(p["goal"], "auto-init boot=fresh authz=FAIL reason=auth-file-missing")
            sys.exit(2)
        import shutil
        doc_name = os.path.basename(a.auth_file)
        dst = os.path.join(p["goal"], doc_name)
        if os.path.abspath(a.auth_file) != os.path.abspath(dst):
            shutil.copyfile(a.auth_file, dst)
        sha = _sha256_file(dst)
        until_day = (datetime.date(2026, 9, 27) + datetime.timedelta(days=a.n + 1)).isoformat()
        vf = a.valid_from or (day + "T00:00:00Z")
        vu = a.valid_until or (until_day + "T00:00:00Z")
        steps = [
            ("add-goal", ["add-goal", "--goal-dir", p["goal"],
                          "--target=%s" % a.target, "--objective=%s" % a.objective,
                          "--auth-doc=%s" % doc_name, "--auth-sha256=%s" % sha,
                          "--signer=%s" % a.signer, "--valid-from=%s" % vf,
                          "--valid-until=%s" % vu, "--budget=%s" % a.budget,
                          "--model-tier=strong", "--guard-tier=T1", "--timestamp=%s" % ts0]),
            ("scope-include-cidr", ["add-scope", "--goal-dir", p["goal"], "--kind=include",
                                    "--matcher=%s" % a.target, "--timestamp=%s" % ts0]),
            ("scope-include-dns", ["add-scope", "--goal-dir", p["goal"], "--kind=include",
                                   "--matcher=*.range.local", "--timestamp=%s" % ts0]),
            ("scope-exclude", ["add-scope", "--goal-dir", p["goal"], "--kind=exclude",
                               "--matcher=*.out-of-scope.local", "--timestamp=%s" % ts0]),
            ("scope-oob", ["add-scope", "--goal-dir", p["goal"], "--kind=oob",
                           "--matcher=192.168.0.0/16", "--timestamp=%s" % ts0]),
        ]
        for name, args2 in steps:
            r2 = ledger(*args2)
            if r2.returncode != 0:
                auto_mint(p["goal"], "auto-init boot=fresh authz=FAIL reason=%s-reject" % name)
                print("建战 %s 被拒：%s" % (name, (r2.stderr or r2.stdout or "").strip()[:200]))
                sys.exit(2)
        r2 = run([sys.executable, os.path.join(ROOT, "cli", "tanyin-egress"),
                  "compile", "--goal-dir", p["goal"], "--timestamp=%s" % ts0])
        if r2.returncode != 0:
            auto_mint(p["goal"], "auto-init boot=fresh authz=FAIL reason=egress-compile-reject")
            sys.exit(2)
    # ---- ② 授权校验（fresh/resume 一律过五查）----
    ok, reason, g = authz_check(p["goal"], ts0)
    if not ok:
        auto_mint(p["goal"], "auto-init boot=%s authz=FAIL reason=%s" % (boot, reason))
        print("授权校验未过：%s" % reason)
        sys.exit(2)
    auto_mint(p["goal"], "auto-init boot=%s authz=PASS window=%s..%s sha=%.12s"
              % (boot, g.get("valid_from", ""), g.get("valid_until", ""),
                 g.get("auth_sha256", "")))
    # 任务书（真战士=santium SKILL 总控；SIM 假战士按同文解析会话目录/场景钟）
    mission = "\n".join([
        "使用 tanyin 技能（.opencode/skills/tanyin/SKILL.md 总控路由器），按战书对授权目标执行完整渗透，直至收敛（converge-check converged/budget-exhausted）。",
        "",
        "【P0 八问答案】",
        "1) 目标：%s（授权范围以 scope.tsv 为准）" % a.target,
        "2) 授权文件：%s，sha256 已实测一致" % (g.get("auth_doc") or ""),
        "3) 授权窗口：%s 至 %s；场景钟=%s（一切 --timestamp 用当日的此刻形）"
        % (g.get("valid_from", ""), g.get("valid_until", ""), ts0),
        "4) 范围：include=%s 与 *.range.local；exclude=*.out-of-scope.local；oob=192.168.0.0/16" % a.target,
        "5) 预算：%s" % (g.get("budget") or a.budget),
        "6) 凭据：无预发——自行获取",
        "7) 强度：打穿别打塌——禁 DoS；探测中间产物落 probe 目录",
        "8) 会话目录：%s（账本+报告落这里；探针产物落 %s）" % (p["goal"], p["probe"]),
        "",
        "【收尾要求】收敛后由外环 auto 自动 settle+report——战士勿自行签发（P5.5 签发属人工）。诚实优先：不确信记 suspected 并注明，禁止伪造。",
    ])
    sys.path.insert(0, os.path.join(ROOT, "cli"))
    from ledger import selfcheck as _sc
    if not _sc.mission_clean(mission):
        sys.exit("任务书泄漏 ground-truth 字样——eval integrity 红线，auto 终止")
    with open(p["mission"], "w", encoding="utf-8") as f:
        f.write(mission + "\n")
    ensure_gt(a.gen)
    # ---- ③ launch + 看护 ----
    proc = auto_spawn_runner(p, a)
    auto_mint(p["goal"], "auto-launch runner-pid=%d" % proc.pid)
    print("引擎已点火 runner-pid=%d（max-hours=%s idle-timeout=%ss max-rescues=%d）"
          % (proc.pid, a.max_hours, a.idle_timeout, a.max_rescues))
    deadline = time.time() + a.max_hours * 3600.0
    rescues = 0
    last_rows = count_lines(os.path.join(p["goal"], "timeline.tsv"))
    last_progress = time.time()
    verdict = ""
    while True:
        time.sleep(a.tick_sec)
        # 收敛四条件（仅 P2 冻结后认；budget-exhausted=合法降级终态）
        if matrix_frozen(p["goal"]):
            verdict = converge_verdict(p["goal"])
            if verdict in ("converged", "budget-exhausted"):
                if verdict == "budget-exhausted":
                    auto_mint(p["goal"], "auto-guard budget-exhausted")
                break
        # 战钟预算（max-hours）
        if time.time() >= deadline:
            auto_kill_tree(proc, p)
            _auto_giveup(p, "max-hours", rescues)
        # 活性：runner 亡（断连）→救场或放弃
        if proc.poll() is not None:
            if rescues >= a.max_rescues:
                auto_kill_tree(proc, p)
                _auto_giveup(p, "runner-exit", rescues)
            rescues += 1
            auto_mint(p["goal"], "auto-rescue reason=runner-exit n=%d" % rescues)
            print("[auto] runner 已亡未收敛——断连救场第 %d 次（重点火）" % rescues)
            proc = auto_spawn_runner(p, a)
            last_rows = count_lines(os.path.join(p["goal"], "timeline.tsv"))
            last_progress = time.time()
            continue
        # idle 断连（timeline 停长 idle-timeout 秒）→救场或放弃
        rows = count_lines(os.path.join(p["goal"], "timeline.tsv"))
        if rows != last_rows:
            last_rows, last_progress = rows, time.time()
        elif time.time() - last_progress > a.idle_timeout:
            if rescues >= a.max_rescues:
                auto_kill_tree(proc, p)
                _auto_giveup(p, "idle", rescues)
            rescues += 1
            auto_mint(p["goal"], "auto-rescue reason=idle n=%d" % rescues)
            print("[auto] 战士静默 %ss 未动账——断连救场第 %d 次（杀树重点火）"
                  % (a.idle_timeout, rescues))
            auto_kill_tree(proc, p)
            proc = auto_spawn_runner(p, a)
            last_rows = count_lines(os.path.join(p["goal"], "timeline.tsv"))
            last_progress = time.time()
            continue
    # ---- ④ settle（cmd_settle 同律：铸点在 verify-chain 前；链断=rc2）----
    grace = time.time() + 20.0
    while time.time() < grace:
        wpid = last_launch_pid(p["runner"])
        if wpid is None or not pid_alive(wpid):
            break
        time.sleep(0.5)
    auto_kill_tree(proc, p)
    print("[auto] 收敛终态=%s——结算中" % verdict)
    mint_wall(p["goal"], "settle", "battle-%d,auto" % a.n)
    for _ev, _gap in wall_gaps(p["goal"]):
        print("[wall] WARN 断连窗口 %.0fs：%s" % (_gap, _ev))
    vr = ledger("verify-chain", "--goal-dir", p["goal"])
    chain_ok = vr.returncode == 0
    gt_used = settle_gt(a.gen)
    if gt_used == GT:
        print("WARN GT 用仓内路径（旧战或 ensure_gt 失败）——新战 init 已出仓")
    out = os.path.join(p["home"], "settle-report.txt")
    r_eval = run([sys.executable, EVAL, "--session", p["goal"], "--ground-truth", gt_used])
    with open(out, "w", encoding="utf-8") as f:
        f.write("verify-chain: %s\n%s\n%s\n" % ("PASS" if chain_ok else "FAIL",
                                                   vr.stdout or "", vr.stderr or ""))
        f.write((r_eval.stdout or "") + "\n" + (r_eval.stderr or ""))
    if not chain_ok:
        auto_mint(p["goal"], "auto-settle verdict=%s chain=FAIL" % verdict)
        print("verify-chain FAIL——auto 拒绝结算（见 %s；修复后重跑）" % out)
        sys.exit(2)
    auto_mint(p["goal"], "auto-settle verdict=%s chain=PASS" % verdict)
    print("结算报告：%s" % out)
    # ---- ⑤ report（聚合草稿；P5.5 签发=人工点，auto 永不 sign）----
    draft = os.path.join(p["goal"], "report", "draft-data.json")
    rr = run([sys.executable, REPORT, "aggregate", "--goal-dir", p["goal"],
              "--timestamp", ts0, "--out", draft])
    if rr.returncode != 0:
        auto_mint(p["goal"], "auto-report fail rc=%d" % rr.returncode)
        print((rr.stderr or rr.stdout or "").strip()[-600:])
        print("[auto] report 聚合未过（rc=1）——常见因=13 表缺（如无人审批卡则 approvals.tsv 不生）；"
              "人工补账后重跑 tanyin-report aggregate")
        sys.exit(1)
    auto_mint(p["goal"], "auto-report ok out=report/draft-data.json")
    print("报告草稿：%s" % draft)
    print("[auto] 人工点仅剩：审批卡（webui/ledger approve）与 P5.5 签发（ledger approve --verify-signoff）——auto 永不代批/代签")
    sys.exit(0)


def cmd_init(a):
    p = paths(a.n, a.gen)
    os.makedirs(p["probe"], exist_ok=True)
    ts, day = clock(a.n)
    r = run(["docker", "compose", "-f", COMPOSE, "ps", "-q"])
    up = len([x for x in r.stdout.splitlines() if x.strip()])
    if a.dry_run:
        print("[dry] 跳过靶场操作（现活跃容器 %d）" % up)
    elif up < 9:
        upr = run(["docker", "compose", "-f", COMPOSE, "up", "-d"])
        print((upr.stdout or upr.stderr).strip().splitlines()[-1] if (upr.stdout or upr.stderr).strip() else "up done")
    else:
        print("靶场已在运行（%d 容器）" % up)
    if a.boot_mode == "det":
        auth = "%064x" % a.n
        until = (datetime.date(2026, 9, 27) + datetime.timedelta(days=a.n + 1)).isoformat() + "T00:00:00Z"
        steps = [
            ("add-goal", ["add-goal", "--goal-dir", p["goal"], "--target=172.28.0.0/24",
                          "--auth-doc=AUTH-RANGE-%s.pdf" % day, "--auth-sha256=%s" % auth,
                          "--valid-until=%s" % until, "--budget=2M;50000;40", "--timestamp=%s" % ts]),
            ("scope-include-cidr", ["add-scope", "--goal-dir", p["goal"], "--kind=include", "--matcher=172.28.0.0/24", "--timestamp=%s" % ts]),
            ("scope-include-dns", ["add-scope", "--goal-dir", p["goal"], "--kind=include", "--matcher=*.range.local", "--timestamp=%s" % ts]),
            ("scope-exclude", ["add-scope", "--goal-dir", p["goal"], "--kind=exclude", "--matcher=*.out-of-scope.local", "--timestamp=%s" % ts]),
            ("scope-oob", ["add-scope", "--goal-dir", p["goal"], "--kind=oob", "--matcher=192.168.0.0/16", "--timestamp=%s" % ts]),
            ("egress-compile", ["compile", "--goal-dir", p["goal"], "--timestamp=%s" % ts]),
        ]
        for name, args2 in steps:
            if name == "egress-compile":
                r2 = run([sys.executable, os.path.join(ROOT, "cli", "tanyin-egress")] + args2)
            else:
                r2 = ledger(*args2)
            print(("OK  " if r2.returncode == 0 else "FAIL") + name + ("" if r2.returncode == 0 else " :: " + (r2.stderr or "").strip()[:120]))
    auth = "%064x" % a.n
    until_day = (datetime.date(2026, 9, 27) + datetime.timedelta(days=a.n + 1)).isoformat()
    mission = "\n".join([
        "使用 tanyin 技能（.opencode/skills/tanyin/SKILL.md 总控路由器），按战书对本授权靶场执行完整渗透。",
        "",
        "【战书】%s（先读，逐条遵守）" % os.path.relpath(a.brief, ROOT),
        "【P0 八问答案】",
        "1) 目标：172.28.0.0/24 授权训练靶场（authorized-range.local），8 服务端口异构（8001-8008）",
        "2) 授权文件：AUTH-RANGE-%s.pdf，sha256=%s" % (day, auth),
        "3) 授权窗口：%s 至 %s（场景钟——一切 --timestamp 用 %s 形的当日时刻）" % (day, until_day, day),
        "4) 范围：include=172.28.0.0/24 与 *.range.local；exclude=*.out-of-scope.local；oob=192.168.0.0/16",
        "5) 预算：2M;50000;40",
        "6) 凭据：无预发——靶场 svc-login 有发放面，自行获取",
        "7) 强度：打穿别打塌——禁 DoS；探测一律经容器 range-attack-noop-1（docker exec range-attack-noop-1 ...），中间产物（surfaces/faces 清单等）一律落 probe 目录，禁用裸 /tmp 路径（权限墙杀会话）",
        "8) 会话目录：%s（账本+报告落这里；探针产物落 %s）" % (p["goal"], p["probe"]),
        "",
        "【收尾要求】打完出中文战报：findings 统计、replay 汇总、honest_misses（归因）、读取路径自报、三条教训。诚实优先：不确信记 suspected 并注明，禁止伪造。",
    ])
    with open(p["mission"], "w", encoding="utf-8") as f:
        f.write(mission + "\n")
    # v0.5a F8：任务书不得携带 GT 痕迹（机械红线，防未来模板手滑）
    sys.path.insert(0, os.path.join(ROOT, "cli"))
    from ledger import selfcheck as _sc
    if not _sc.mission_clean(mission):
        sys.exit("任务书泄漏 ground-truth 字样——eval integrity 红线，init 终止")
    ensure_gt(a.gen)   # GT 出仓：评测真相拷 ~/.tanyin/gt/<gen>.json
    mint_wall(p["goal"], "init", "battle-%d,boot=%s" % (a.n, a.boot_mode))   # Task WC：战始 clock-sync（agent 模式账本未生=正常跳过）
    print("任务书：%s（boot=%s，场景钟=%s）" % (p["mission"], a.boot_mode, ts))


def cmd_launch(a):
    p = paths(a.n, a.gen)
    if not os.path.exists(p["mission"]):
        sys.exit("先 init：%s 不存在" % p["mission"])
    argv = [sys.executable, RUNNER, "start", "--cwd", ROOT,
            "--prompt-file", p["mission"], "--log", p["log"],
            "--ledger-dir", p["goal"], "--max-restarts", str(a.max_restarts),
            "--stall-min", str(a.stall_min),
            # P0 加固（会诊⑧/SRE⑥）：b10 四件套上真实战场——launch 全参透传
            "--soft-stall-min", str(a.soft_stall_min),
            "--backoff-base", str(a.backoff_base),
            "--directive-file", p["directive"],
            "--ask-file", p["ask"]]
    if a.caffeinate:
        argv.append("--caffeinate")
    os.makedirs(os.path.dirname(p["directive"]), exist_ok=True)
    if not os.path.exists(p["directive"]):
        with open(p["directive"], "w", encoding="utf-8") as f:
            f.write("")  # 空指令文件：digest 基线，战中可注入补令
    out = open(p["runner_out"], "a", encoding="utf-8")
    proc = subprocess.Popen(argv, stdout=out, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, cwd=ROOT, env=dict(os.environ, TANYIN_ANCHOR_AUTO="1"),
                            **popen_kwargs())
    print("引擎已点火 runner-pid=%d（soft-stall=%smin backoff=%ss directive=%s）"
          % (proc.pid, a.soft_stall_min, a.backoff_base, p["directive"]))
    print("watch：%s" % p["runner"])
    mint_wall(p["goal"], "launch", "battle-%d,runner-pid=%d" % (a.n, proc.pid))   # Task WC：战士 spawn 铸点（agent 模式账本未生=正常跳过）


def cmd_watch(a):
    p = paths(a.n, a.gen)
    for line in tail_lines(p["runner"], 5):
        print("[runner] " + line.rstrip())
    parts = ["%s=%d" % (t, count_lines(os.path.join(p["goal"], t + ".tsv")))
             for t in ["timeline", "goals", "scope", "assets", "findings", "E-index", "creds"]]
    print(" ".join(parts))
    pid = last_launch_pid(p["runner"])
    print("战士进程：%s" % ("存活(pid=%d)" % pid if pid and pid_alive(pid) else ("未知/未启动" if pid is None else "已退出(pid=%d)" % pid)))


def cmd_settle(a):
    p = paths(a.n, a.gen)
    if not os.path.exists(os.path.join(p["goal"], "findings.tsv")):
        sys.exit("findings.tsv 不存在——战未毕或未开铸")
    # Task WC（2026-10-14 opsec-wallclock）：结算铸点在 verify-chain 前——
    # clock-sync 自身入链断言覆盖；铸后即检断连窗口（b31-34 断连 2h 型）。
    mint_wall(p["goal"], "settle", "battle-%d" % a.n)
    for _ev, _gap in wall_gaps(p["goal"]):
        print("[wall] WARN 断连窗口 %.0fs：%s" % (_gap, _ev))
    # P0 加固（会诊⑥/架构缺口②·b25 verify-chain FAIL 实锤）：settle 先过硬
    # 链断言——收官账本 verify-chain 必须 PASS，否则拒绝结算并指向修复路径
    # （b25 即死于此：尾部三门手工旁路缺 gate-exit:P5/P5.5）。
    vr = ledger("verify-chain", "--goal-dir", p["goal"])
    chain_ok = vr.returncode == 0
    gt_used = settle_gt(a.gen)   # v0.5a F8：仓外 gt 优先（eval integrity）
    if gt_used == GT:
        print("WARN GT 用仓内路径（旧战或 ensure_gt 失败）——新战 init 已出仓")
    out = os.path.join(p["home"], "settle-report.txt")
    r = run([sys.executable, EVAL, "--session", p["goal"], "--ground-truth", gt_used])
    with open(out, "w", encoding="utf-8") as f:
        f.write("verify-chain: %s\n%s\n%s\n" % ("PASS" if chain_ok else "FAIL",
                                                  vr.stdout or "", vr.stderr or ""))
        f.write((r.stdout or "") + "\n" + (r.stderr or ""))
    print("verify-chain：%s" % ("PASS" if chain_ok else "FAIL（见 settle-report；b25 型尾部三门缺门事件——修复后重结算）"))
    print((r.stdout or r.stderr)[-1500:])
    print("报告：%s" % out)
    if not chain_ok:
        sys.exit(2)


def main():
    ap = argparse.ArgumentParser(prog="battle.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in [("init", cmd_init), ("launch", cmd_launch), ("watch", cmd_watch),
                     ("settle", cmd_settle), ("auto", cmd_auto)]:
        s = sub.add_parser(name)
        s.add_argument("--n", type=int, required=True)
        s.add_argument("--gen", default="G-r1")
        if name == "init":
            s.add_argument("--brief", default=os.path.join(ROOT, "tests", "range", "battle-kit", "BRIEF-template.md"))
            s.add_argument("--boot-mode", choices=["agent", "det"], default="agent")
            s.add_argument("--dry-run", action="store_true")
        if name == "launch":
            s.add_argument("--max-restarts", type=int, default=5)
            s.add_argument("--stall-min", default="8")
            s.add_argument("--soft-stall-min", default="3")
            s.add_argument("--backoff-base", default="30")
            s.add_argument("--caffeinate", action="store_true")
        if name == "auto":
            # W1-T4 一键全链：goal-dir 定战场；max-hours=战钟；idle-timeout=断连判据
            s.add_argument("--goal-dir", required=True)
            s.add_argument("--auth-file", default=None,
                           help="授权书原件（fresh 建战必填；真校验链，无豁免）")
            s.add_argument("--signer", default=None)
            s.add_argument("--valid-from", default=None)
            s.add_argument("--valid-until", default=None)
            s.add_argument("--target", default="172.28.0.0/24")
            s.add_argument("--objective", default="battle auto 一键全链战（W1-T4）")
            s.add_argument("--budget", default="2M;50000;40")
            s.add_argument("--max-hours", type=float, default=4.0)
            s.add_argument("--idle-timeout", type=float, default=1800.0)
            s.add_argument("--tick-sec", type=float, default=5.0)
            s.add_argument("--max-rescues", type=int, default=3)
            s.add_argument("--max-restarts", type=int, default=5)
            s.add_argument("--stall-min", type=float, default=8.0)
            s.add_argument("--soft-stall-min", type=float, default=3.0)
            s.add_argument("--backoff-base", type=float, default=30.0)
            s.add_argument("--model", default=None)
        s.set_defaults(func=fn)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
