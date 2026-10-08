#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""battle.py · 全战外环 v2（B4）——22 战手工循环的代码化

一条命令一整战：init（起靶+铸 P0 或生成任务书）→ launch（引擎托管开战）
→ watch（战况）→ settle（评分+归因初稿）。

用法示例（battle-23 / G-r24）：
  python3 scripts/battle.py init  --n 23 --gen G-r24 --brief tests/range/battle-kit/BRIEF-template.md
  python3 scripts/battle.py launch --n 23
  python3 scripts/battle.py watch  --n 23
  python3 scripts/battle.py settle --n 23

场景钟：battle N = 2026-09-27 + N 天 09:00Z（b22=10-19 实测锚定）。
boot 双模：agent（默认，总控自跑 P0——run4 实证）/ det（脚本代铸，总控从 P1 续）。
"""
import argparse
import datetime
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
RUNNER = os.path.join(ROOT, "cli", "tanyin-runner")
COMPOSE = os.path.join(ROOT, "tests", "range", "docker-compose.yml")
GT = os.path.join(ROOT, "tests", "range", "ground-truth.json")
EVAL = os.path.join(ROOT, "tests", "eval_range_recall.py")
BASE = "/tmp/tanyin-range-battle"


def clock(n):
    d = datetime.date(2026, 9, 27) + datetime.timedelta(days=n)
    return d.strftime("%Y-%m-%dT09:00:00Z"), d.strftime("%Y-%m-%d")


def paths(n, gen):
    home = os.path.join(BASE, "battle-%d" % n)
    return {
        "home": home,
        "goal": os.path.join(home, gen),
        "probe": os.path.join(home, "probe"),
        "mission": os.path.join(home, "mission.txt"),
        "log": os.path.join(home, "opencode-run.log"),
        "runner": os.path.join(home, "opencode-run.log.runner.tsv"),
    }


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)


def cmd_init(a):
    p = paths(a.n, a.gen)
    os.makedirs(p["probe"], exist_ok=True)
    ts, day = clock(a.n)
    rng = sh("docker compose -f %s ps -q 2>/dev/null | wc -l" % COMPOSE)
    up = int(rng.stdout.strip() or 0)
    if a.dry_run:
        print("[dry] 跳过靶场操作（现活跃容器 %d）" % up)
    elif up < 9:
        print(sh("docker compose -f %s up -d 2>&1 | tail -1" % COMPOSE).stdout.strip())
    else:
        print("靶场已在运行（%d 容器）" % up)
    if a.boot_mode == "det":
        auth = ("%x" % a.n) * 64
        for c in [
            "%s add-goal --goal-dir %s --target=172.28.0.0/24 --auth-doc=AUTH-RANGE-%s.pdf --auth-sha256=%s --valid-until=%sT00:00:00Z --budget=2M;50000;40 --timestamp=%s" % (LEDGER, p["goal"], day, auth, (datetime.date(2026, 9, 27) + datetime.timedelta(days=a.n + 1)).isoformat(), ts),
            "%s add-scope --goal-dir %s --kind=include --matcher=172.28.0.0/24 --timestamp=%s" % (LEDGER, p["goal"], ts),
            "%s add-scope --goal-dir %s --kind=include --matcher=*.range.local --timestamp=%s" % (LEDGER, p["goal"], ts),
            "%s add-scope --goal-dir %s --kind=exclude --matcher=*.out-of-scope.local --timestamp=%s" % (LEDGER, p["goal"], ts),
            "%s add-scope --goal-dir %s --kind=oob --matcher=192.168.0.0/16 --timestamp=%s" % (LEDGER, p["goal"], ts),
            "python3 %s/../../cli/tanyin-egress compile --goal-dir %s --timestamp=%s" % (LEDGER, p["goal"], ts),
        ]:
            r = sh(c)
            print(("OK  " if r.returncode == 0 else "FAIL") + " " + c.split()[1] if len(c.split()) > 1 else c)
    mission = "\n".join([
        "使用 tanyin 技能（.opencode/skills/tanyin/SKILL.md 总控路由器），按战书对本授权靶场执行完整渗透。",
        "",
        "【战书】%s（先读，逐条遵守）" % os.path.relpath(a.brief, ROOT),
        "【P0 八问答案】",
        "1) 目标：172.28.0.0/24 授权训练靶场（authorized-range.local），8 服务端口异构（8001-8008）",
        "2) 授权文件：AUTH-RANGE-%s.pdf，sha256=%s" % (day, ("%x" % a.n) * 64),
        "3) 授权窗口：%s 至次日（场景钟——一切 --timestamp 用 %s 形的当日时刻）" % (day, day),
        "4) 范围：include=172.28.0.0/24 与 *.range.local；exclude=*.out-of-scope.local；oob=192.168.0.0/16",
        "5) 预算：2M;50000;40",
        "6) 凭据：无预发——靶场 svc-login 有发放面，自行获取",
        "7) 强度：打穿别打塌——禁 DoS；探测一律经容器 range-attack-noop-1（docker exec range-attack-noop-1 ...），宿主不得直连 172.28.0.x",
        "8) 会话目录：%s（账本+报告落这里；探针产物落 %s/）" % (p["goal"], p["probe"]),
        "",
        "【收尾要求】打完出中文战报：findings 统计、replay 汇总、honest_misses（归因）、读取路径自报、三条教训。诚实优先：不确信记 suspected 并注明，禁止伪造。",
    ])
    with open(p["mission"], "w", encoding="utf-8") as f:
        f.write(mission + "\n")
    print("任务书：%s（boot=%s，场景钟=%s）" % (p["mission"], a.boot_mode, ts))


def cmd_launch(a):
    p = paths(a.n, a.gen)
    if not os.path.exists(p["mission"]):
        sys.exit("先 init：%s 不存在" % p["mission"])
    cmd = ("nohup python3 %s start --cwd %s --prompt-file %s --log %s --ledger-dir %s "
           "--max-restarts %d --stall-min %s > %s/runner.out 2>&1 & echo $!") % (
        RUNNER, ROOT, p["mission"], p["log"], p["goal"], a.max_restarts, a.stall_min, p["home"])
    r = sh(cmd)
    print("引擎已点火 runner-pid=%s" % r.stdout.strip())
    print("watch：%s" % p["runner"])


def cmd_watch(a):
    p = paths(a.n, a.gen)
    for line in sh("tail -5 %s 2>/dev/null" % p["runner"]).stdout.splitlines():
        print("[runner] " + line)
    parts = []
    for t in ["timeline", "goals", "scope", "assets", "findings", "E-index", "creds"]:
        fp = os.path.join(p["goal"], t + ".tsv")
        try:
            parts.append("%s=%d" % (t, sum(1 for _ in open(fp, encoding="utf-8"))))
        except OSError:
            parts.append("%s=0" % t)
    print(" ".join(parts))
    alive = sh("pgrep -f 'opencode run' | wc -l").stdout.strip()
    print("opencode 进程数：%s" % alive)


def cmd_settle(a):
    p = paths(a.n, a.gen)
    if not os.path.exists(os.path.join(p["goal"], "findings.tsv")):
        sys.exit("findings.tsv 不存在——战未毕或未开铸")
    out = os.path.join(p["home"], "settle-report.txt")
    r = sh("python3 %s --session %s --ground-truth %s" % (EVAL, p["goal"], GT))
    with open(out, "w", encoding="utf-8") as f:
        f.write(r.stdout + "\n" + r.stderr)
    print(r.stdout[-2000:] if r.stdout else r.stderr[-500:])
    print("报告：%s" % out)


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
        s.set_defaults(func=fn)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
