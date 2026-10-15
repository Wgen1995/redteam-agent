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
import os
import subprocess
import sys

IS_WIN = os.name == "nt"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
RUNNER = os.path.join(ROOT, "cli", "tanyin-runner")
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
    for name, fn in [("init", cmd_init), ("launch", cmd_launch), ("watch", cmd_watch), ("settle", cmd_settle)]:
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
        s.set_defaults(func=fn)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
