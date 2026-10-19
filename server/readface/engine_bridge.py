# -*- coding: utf-8 -*-
"""engine_bridge(P0 T6)——读面写转发子进程(单写者纪律的执行面)。

铁律对齐(docs/superpowers/plans/2026-10-20-p0-command-deck.md):
- 写路径一律本桥子进程调 tanyin 命令链(tanyin-ledger …);读面 FastAPI
  进程零账本直写——say.py 只 subprocess 本脚本,不碰 battles 根。
- 引擎零改: 本桥只拼既有命令面参数,不改 cli/ 一行。
- P0 一律 --dry-run: 演练=算战号+拼 battle/new 链(add-goal+add-scope)
  回执,零目录零账本写入;真点火(fail-closed 拒,后续舰接线)。

CLI(仓库根):
  python3 server/readface/engine_bridge.py ignite \
      --target <目标> [--scope <匹配> ...] [--budget <预算句>] \
      [--note <说明>] --dry-run
  python3 server/readface/engine_bridge.py approve \
      --battle <battle-N> --command-hash <sha256hex> \
      --decision approved|rejected [--note <补充说明>]
    (T8 内联审批: 键=sha256(revert_cmd) 同 ledger_reader.approvals_pending
     的 id;真写 approvals.tsv+timeline 链——note 落事件原文锚,引擎 webui
     W6「决定回链」同律,待审队列据此消项)
  python3 server/readface/engine_bridge.py steer       --battle <battle-N> --text <插话原文> [--intent <target_intent 线索>]
    (T10 插话转向: 真写 timeline warrior-steer 行,仗内全部在编战士逐个
     fan-out,无在编缺省 w1(引擎 webui 同律);原文必达,账本战士每轮
     模型调用前 scan 消费)
  python3 server/readface/engine_bridge.py halt       --battle <battle-N> [--reason <停仗原因>]
    (T10 全停该仗: 真写 warrior-stop 行(逐战士)+deck-halt 留痕行,
     在跑战士 scan 即停;停信号=steer.py 单源,引擎零改)
stdout 末行=JSON 回执;rc: 0=演练成/审批成/入链成 / 2=用法或 fail-closed/拒收。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

# 仓根 cli/ 前上 sys.path(ledger_reader 同款先例),复用 battles 根单源。
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
_CLI_DIR = os.path.join(_REPO_ROOT, "cli")
if _CLI_DIR not in sys.path:
    sys.path.insert(0, _CLI_DIR)

from ledger import timeline as ledger_timeline      # noqa: E402
from ledger.session_view import default_battles_dir   # noqa: E402
from warrior import steer as warrior_steer          # noqa: E402

_LEDGER_CLI = os.path.join(_CLI_DIR, "tanyin-ledger")
_GEN_OF_NEW_BATTLE = "G-w1"     # 引擎 webui server.py 同位约定


def _emit(doc):
    print(json.dumps(doc, ensure_ascii=False))


def _next_battle_no(root):
    """根上最大 battle-N +1(引擎 webui _post_battle_new 同式)。"""
    try:
        nums = [int(m.group(1)) for e in os.listdir(root)
                for m in [re.match(r"^battle-(\d+)$", e)] if m]
    except OSError:
        nums = []
    return (max(nums) + 1) if nums else 1


def _ignite_chain(n, target, scopes, budget, note):
    """battle/new 链 argv 演练(引擎 webui 钮 1 同形;授权件字段=待补清单)。"""
    goal_dir = os.path.join(default_battles_dir(), "battle-%d" % n,
                            _GEN_OF_NEW_BATTLE)
    add_goal = [
        sys.executable, _LEDGER_CLI, "add-goal", "--goal-dir", goal_dir,
        "--target=" + target,
        "--objective=" + (note or "（说话开仗,未填说明）"),
        # 授权八问字段真点火时由授权件补齐(确认卡授权提示同源)——
        # dry-run 回执只报已知量,不编 sha/签名人。
        "--budget=<授权时定>",
        "--timestamp=<点火时>"]
    if budget:
        add_goal.append("--business-context=预算说明:" + budget)
    chain = [add_goal]
    for s in scopes:
        chain.append([
            sys.executable, _LEDGER_CLI, "add-scope", "--goal-dir", goal_dir,
            "--kind=include", "--matcher=" + s,
            "--note=说话开仗确认卡范围", "--timestamp=<点火时>"])
    return chain


def cmd_ignite(args):
    if not args.target.strip():
        _emit({"ok": False, "error": "target 必填(开仗目标不可为空)"})
        return 2
    if not args.dry_run:
        # fail-closed: 真点火 P0 未接线(授权件链/仲裁/runner 后续舰)。
        _emit({"ok": False, "error":
               "真点火未接线——P0 一律 --dry-run 演练;"
               "授权件+预算仲裁+runner spawn 见后续舰"})
        return 2
    root = default_battles_dir()
    n = _next_battle_no(root)
    chain = _ignite_chain(n, args.target.strip(),
                          [s.strip() for s in args.scope if s.strip()],
                          (args.budget or "").strip(), (args.note or "").strip())
    _emit({"ok": True, "dry_run": True, "battle": n,
           "battles_root": root,
           "goal_dir": os.path.join(root, "battle-%d" % n,
                                    _GEN_OF_NEW_BATTLE),
           "chain": [" ".join(step) for step in chain],
           "missing_for_real": [
               "auth-doc", "auth-sha256", "signer", "valid-from",
               "valid-until", "model-tier", "guard-tier"],
           "note": "P0 一律 dry-run: 链已演练(战号+参数),零目录零账本写入"})
    return 0


# ---------------------------------------------------------------- ② approve --

# 指挥台审批通道只发批/拒(exempted=预授权豁免走引擎 preauth,
# knowledge-approved=知识审批,皆非本通道——词表收紧不放宽)。
_APPROVE_DECISIONS = ("approved", "rejected")
_APPROVER = "操作员(指挥台)"          # 引擎 webui「操作员(观察面)」同位约定
_CLI_TIMEOUT_S = 50                   # tanyin-ledger 子进程帽(单写者+锁)
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def _latest_gen(battle_home):
    """战目录内最新代 goal 目录(G-* 自然序;引擎 webui _latest_gen 同式)。"""
    def _key(name):
        digits = [int(d) for d in re.findall(r"\d+", name)]
        return (digits or [0])[0]
    try:
        gens = [d for d in os.listdir(battle_home)
                if d.startswith("G-") and os.path.isdir(os.path.join(battle_home, d))]
    except OSError:
        return None
    if not gens:
        return None
    return os.path.join(battle_home, sorted(gens, key=_key)[-1])


def _approval_sig(command_hash, key_text):
    """--sig=HMAC-SHA256(sha256(key), command_hash)——CLI write_cmds.
    _approval_sig 单源语义(webui server._approval_sig/preauth._sig 同式),
    持钥环境(TANYIN_APPROVAL_KEY 在场)由 CLI 自验自存 sig 段。
    """
    import hashlib
    import hmac
    return hmac.new(hashlib.sha256(key_text.encode("utf-8")).digest(),
                    command_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def _tl_count(goal_dir):
    """timeline 行数(回执行号=文件实况;引擎 webui _tl_count 同式)。"""
    try:
        with open(os.path.join(goal_dir, "timeline.tsv"), encoding="utf-8") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def cmd_approve(args):
    # 本目录读投影(脚本运行 sys.path[0]=server/readface;守位不重插)。
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import ledger_reader                      # 待审单源(id=sha256(revert_cmd))

    chash = (args.command_hash or "").strip()
    if not _HEX64_RE.match(chash):
        _emit({"ok": False, "error": "command-hash 须为 sha256hex(64 位十六进制)"})
        return 2
    if args.decision not in _APPROVE_DECISIONS:
        _emit({"ok": False, "error":
               "decision 须 approved|rejected(指挥台只发批/拒): %s" % args.decision})
        return 2
    battle = (args.battle or "").strip()
    if not battle:
        _emit({"ok": False, "error": "battle 必填(如 battle-2)"})
        return 2
    battle_home = os.path.join(default_battles_dir(), battle)
    goal_dir = _latest_gen(battle_home)
    if goal_dir is None:
        _emit({"ok": False, "error": "战目录无 goal 代目录(G-*): %s" % battle})
        return 2
    # 待审单源读回: 哈希不在队(已决/已核销/换代)→拒收不落笔。
    pending = ledger_reader.approvals_pending(goal_dir)
    item = next((it for it in pending if it["id"] == chash), None)
    if item is None:
        _emit({"ok": False,
               "error": "command_hash 不在待审队列(可能已决/已核销/换代): %s" % chash,
               "battle": battle, "pending": len(pending)})
        return 2
    # note=事件原文锚+（指挥台审批）——引擎 webui _post_approval 落笔式
    # (note 含原事件文本=W6 决定回链键,待审投影据此消项)。
    note = "%s（指挥台审批）" % item["event"]
    if (args.note or "").strip():
        note += "；补充:" + args.note.strip()
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    argv = [sys.executable, _LEDGER_CLI, "approve", "--goal-dir", goal_dir,
            "--command-hash=" + chash, "--decision=" + args.decision,
            "--approver=" + _APPROVER, "--timestamp=" + ts,
            "--note=" + note]
    akey = os.environ.get("TANYIN_APPROVAL_KEY", "")
    if akey:                                   # 持钥环境: 自动签发(CLI 自验)
        argv.append("--sig=" + _approval_sig(chash, akey))
    try:
        cp = subprocess.run(argv, capture_output=True, text=True,
                            timeout=_CLI_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        _emit({"ok": False,
               "error": "tanyin-ledger approve 子进程超时(%ds)" % _CLI_TIMEOUT_S})
        return 2
    out = ((cp.stdout or "") + (cp.stderr or "")).strip()
    first = (cp.stdout or "").splitlines()
    rid = first[0].split("\t")[1] \
        if first and first[0].startswith("OK\t") else ""
    if cp.returncode != 0 or not rid:
        _emit({"ok": False, "error": "引擎拒收审批(rc=%d): %s"
               % (cp.returncode, out[:300])})
        return 2
    _emit({"ok": True, "cmd": "approve", "battle": battle,
           "goal_dir": goal_dir, "decision": args.decision,
           "command_hash": chash, "approval_id": rid,
           "event": item["event"], "approver": _APPROVER,
           "timeline_row": _tl_count(goal_dir),
           "note": "审批已入链(%s);待审队列读回自然消项" % rid})
    return 0


# ---------------------------------------------------------------- ③ steer/halt --

# CLI 面实勘(T10): tanyin-ledger 无 steer/stop 子命令——插话/停令写面单源=
# cli/warrior/steer.py write_steer/write_stop(引擎 webui /api/v2/steer-reply
# 与 fleet supervisor._signal 同款调用)。本桥=读面唯一写出口的子进程,
# 进程内调该单源写函数(goal 锁 append_tl_locked 单写者),零私铸 TSV,
# 引擎零改。事件形(steer.py 单源):
#   warrior-steer target=<warrior-id> text=<单行>   actor=总控 phase=P3
#   warrior-stop warrior=<warrior-id> reason=<单行> actor=总控 phase=P3
# halt 另铸 deck-halt 留痕行(supervisor._signal 的 fleet-stop 同律)。

_STEER_DEFAULT_WARRIOR = "w1"     # 账本无在编战士时的缺省目标(引擎 webui
                                  # steer_reply「warrior or "w1"」同律缺省)
_DEFAULT_HALT_REASON = "指挥台全停"
# 仗内在编战士判读(supervisor._warriors 同律: warrior-start/heartbeat 事件源)
_WARRIOR_EV_RE = re.compile(r"^warrior-(?:start|heartbeat)\s+.*?warrior=(\S+)")


def _battle_warriors(goal_dir):
    """仗账本可见的全部战士 id(warrior-start/heartbeat 事件源,supervisor 同律)。"""
    out = set()
    try:
        rows = ledger_timeline.read_rows(goal_dir)
    except Exception:                              # noqa: BLE001 账本未生=无战士
        return []
    for r in rows:
        if len(r) < 4:
            continue
        m = _WARRIOR_EV_RE.match(r[3])
        if m:
            out.add(m.group(1))
    return sorted(out)


def _resolve_battle(battle):
    """仗名 → (goal_dir|None, error|None): 空名/无代目录 fail-closed。"""
    battle = (battle or "").strip()
    if not battle:
        return None, "battle 必填(如 battle-3)"
    goal_dir = _latest_gen(os.path.join(default_battles_dir(), battle))
    if goal_dir is None:
        return None, "战目录无 goal 代目录(G-*): %s" % battle
    return goal_dir, None


def cmd_steer(args):
    goal_dir, err = _resolve_battle(args.battle)
    if err is not None:
        _emit({"ok": False, "error": err})
        return 2
    text = (args.text or "").strip()
    if not text:
        _emit({"ok": False, "error": "text 必填(插话内容不可为空)"})
        return 2
    warriors = _battle_warriors(goal_dir) or [_STEER_DEFAULT_WARRIOR]
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        for wid in warriors:                        # 原文必达: 战士领原话
            warrior_steer.write_steer(goal_dir, wid, text, ts)
    except Exception as e:                          # noqa: BLE001 fail-closed 如实
        _emit({"ok": False, "battle": args.battle.strip(),
               "error": "插话入链失败(引擎拒收/fail-closed): %s" % e})
        return 2
    _emit({"ok": True, "cmd": "steer", "battle": args.battle.strip(),
           "goal_dir": goal_dir, "warriors": warriors,
           "timeline_row": _tl_count(goal_dir), "text": text,
           "intent": (args.intent or "").strip(),
           "note": "插话已入链(目标战士 %s);账本战士每轮模型调用前 scan 消费"
                   % ",".join(warriors)})
    return 0


def cmd_halt(args):
    battle = (args.battle or "").strip()
    goal_dir, err = _resolve_battle(battle)
    if err is not None:
        _emit({"ok": False, "error": err})
        return 2
    reason = (args.reason or "").strip() or _DEFAULT_HALT_REASON
    warriors = _battle_warriors(goal_dir)           # 无在编=只铸留痕行(如实)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        for wid in warriors:
            warrior_steer.write_stop(goal_dir, wid, reason, ts)
        ledger_timeline.append_tl_locked(           # 全停留痕(supervisor 同律)
            goal_dir, ts,
            "deck-halt battle=%s reason=%s" % (
                battle, " ".join(reason.split())),
            actor=warrior_steer.ACTOR, phase="P-lifecycle")
    except Exception as e:                          # noqa: BLE001 fail-closed 如实
        _emit({"ok": False, "battle": battle,
               "error": "全停入链失败(引擎拒收/fail-closed): %s" % e})
        return 2
    _emit({"ok": True, "cmd": "halt", "battle": battle,
           "goal_dir": goal_dir, "stopped": warriors,
           "timeline_row": _tl_count(goal_dir), "reason": reason,
           "note": "全停信号已入链(warrior-stop→%s+deck-halt 留痕);"
                   "在跑战士 scan 即停" % (",".join(warriors) or "无在编")})
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="engine_bridge")
    sub = p.add_subparsers(dest="cmd")
    ig = sub.add_parser("ignite", help="开仗(battle/new 链)")
    ig.add_argument("--target", default="", help="开仗目标(域名/IP/系统)")
    ig.add_argument("--scope", action="append", default=[],
                    help="范围匹配(可重复)")
    ig.add_argument("--budget", default="", help="预算说明句")
    ig.add_argument("--note", default="", help="补充说明")
    ig.add_argument("--dry-run", action="store_true",
                    help="演练不落账(P0 唯一允许模式)")
    ap = sub.add_parser("approve", help="内联审批(approve 链,真写)")
    ap.add_argument("--battle", default="", help="仗目录名(如 battle-2)")
    ap.add_argument("--command-hash", default="",
                    help="待审命令哈希=sha256(revert_cmd),64 位 hex")
    ap.add_argument("--decision", default="",
                    help="approved|rejected(指挥台只发批/拒)")
    ap.add_argument("--note", default="", help="操作员补充说明(入链)")
    st = sub.add_parser("steer", help="插话转向(warrior-steer 链,真写)")
    st.add_argument("--battle", default="", help="仗目录名(如 battle-3)")
    st.add_argument("--text", default="", help="插话原文(必达战士,单行折叠)")
    st.add_argument("--intent", default="",
                    help="target_intent 线索(回执留痕,不入链)")
    ht = sub.add_parser("halt", help="全停该仗(warrior-stop+deck-halt 链,真写)")
    ht.add_argument("--battle", default="", help="仗目录名(如 battle-3)")
    ht.add_argument("--reason", default="", help="停仗原因(缺省=指挥台全停)")
    args = p.parse_args(argv)
    if args.cmd == "ignite":
        return cmd_ignite(args)
    if args.cmd == "approve":
        return cmd_approve(args)
    if args.cmd == "steer":
        return cmd_steer(args)
    if args.cmd == "halt":
        return cmd_halt(args)
    p.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
