# -*- coding: utf-8 -*-
"""执行入口卡层门链（W3②：卡片调用必过现有执法层）。

分工律（防两份解释漂移——enforce.py 单源先例）：
  卡层自有门（本模块）：unknown-tool → deny-extra（卡黑名单覆盖） →
    supply-chain（在役+lock 现场复验） → card-rate（限速旗标固化） →
    approval-required（L3 档审批门挂卡：approvals.tsv command_hash 对照）。
  委托层（execute() → tanyin-guard exec）：四层 scope（Tier1 同源
    out_of_scope_hosts/load_scope）+ 全局副作用黑名单（deny_forms/deny_hit）+
    nuclei 参数门/限速滑窗/时间旅行/凭据覆盖面——guard 既有门链原样生效，
    卡层零复制。

审批哈希口径：command_hash = sha256(argv 空格连接串)——与
tanyin-ledger approve --command-hash 同一命令面（操作员持钥人审通道）。
"""
import hashlib
import os

from . import cards as tool_cards
from . import install as tool_install
from . import lock as tool_lock

TAB = chr(9)


def command_hash(argv):
    """审批绑定哈希：argv 规范串（空格连接）sha256 hex——approve 同口径。"""
    return hashlib.sha256(" ".join(str(a) for a in argv).encode("utf-8")).hexdigest()


def _approval_row(session, chash):
    """approvals.tsv 中 decision=approved 且 command_hash 逐字对照的首行（AP id）；
    无=None。遗留行（他哈希）不放行——审批绑定命令不绑定卡。"""
    from ledger.schemas import TABLES
    af = TABLES["approvals.tsv"]
    ci, di = af.index("command_hash"), af.index("decision")
    ii = af.index("id") if "id" in af else None
    for r in session.rows("approvals.tsv"):
        if r[di] == "approved" and r[ci] == chash:
            return r[ii] if ii is not None else "AP-?"
    return None


def _deny_extra_hit(card, argv):
    """卡黑名单覆盖：卡 deny_extra 模式对 joined argv 的子串命中（全局
    DENYLIST 不在此重复——guard 委托层单源执法）。"""
    joined = " ".join(str(a) for a in argv)
    for pat in card.deny_extra or []:
        if pat and pat in joined:
            return pat
    return None


def _missing_rate_flags(card, argv):
    """限速旗标固化（OP1 nuclei -rl 先例的卡面泛化）：卡声明 rate_flags 者，
    argv 必含该旗标（值任意——门只锁「有限速」不锁数值档，数值档=RoE 披露面）。"""
    return [f for f in (card.rate_flags or []) if f not in argv]


def card_gate(goal_dir, name, args, ts, state_path=None, lock_path=None,
              pub=None, session=None):
    """卡层门链（纯判定，不落账不执行——审计/执行由 execute() 负责）。

    返回 (ok, reason)：ok=True 时 reason="ok"。门序=安全优先：
    未注册 → 卡黑名单 → 供应链（在役+lock 复验） → 限速旗标 → L3 审批。
    ts 参数为审计口径保留（时间旅行门在 guard 委托层执法，卡层不复制）。
    """
    card = tool_cards.get_card(name)
    if card is None:
        return False, ("unknown-tool: %r 不在注册表（25 卡清单外拒执行）" % name)
    argv = [card.binary] + [str(a) for a in args]
    hit = _deny_extra_hit(card, argv)
    if hit:
        return False, "deny-extra 命中: %s（卡 %s 黑名单覆盖）" % (hit, card.name)
    if not tool_install.is_installed(card, state_path=state_path):
        return False, ("card-not-installed: %s 未装卡（装卡验签=tanyin-tools install）"
                       % card.name)
    ok, why = tool_lock.verify_card(card, lock_path, pub)
    if not ok:
        return False, "supply-chain: %s" % why
    missing = _missing_rate_flags(card, argv)
    if missing:
        return False, ("card-rate: %s 缺限速旗标 %s（卡限速 %s 固化执法）"
                       % (card.name, " ".join(missing), card.rate))
    if card.requires_approval:
        try:
            from ledger import core
            sess = session or core.Session(goal_dir)
        except ImportError as e:
            return False, ("approval-required: L3 卡审批账不可达（fail-closed）: %s" % e)
        ap = _approval_row(sess, command_hash(argv))
        if not ap:
            return False, ("approval-required: L3 卡 %s 未批即拒"
                           "（approve --command-hash %s 后方可执行）"
                           % (card.name, command_hash(argv)))
    return True, "ok"


def _guard_spawn(argv):
    """真执行器：tanyin-guard exec 子进程（guard 自带脱敏/取票/门链）。"""
    import subprocess
    r = subprocess.run(argv, capture_output=True, text=True, timeout=600,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout or "", r.stderr or ""


def _append_tl(gd, ts, event, revert=""):
    """timeline 落账（ledger.timeline 单源；guard append_tl 同律 O(1) 尾追加）。"""
    from ledger.timeline import append_tl_locked
    append_tl_locked(gd, ts, event, actor="tools", phase="P3", revert=revert)


def _reject_event(name, reason):
    """tools-reject 事件行（guard-reject 同型；TAB/换行清洗防列破格）。"""
    flat = " ".join(str(reason).split())
    return ("tools-reject card=%s %s" % (name, flat)).strip()


def _sys_exe():
    import sys
    return sys.executable


def _guard_entry():
    return os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tanyin-guard")


def execute(goal_dir, name, args, ts, spawn=None, state_path=None,
            lock_path=None, pub=None):
    """工具卡执行入口（W3②：卡片调用必过现有执法层）。

    门序：卡层门链（card_gate）→ 委托 tanyin-guard exec（四层 scope/全局
    deny-list/nuclei 参数/限速滑窗/时间旅行/凭据覆盖面=guard 既有门链零复制）
    → 成功且卡带 revert 义务时落账核销义务（P6.0 清理律的义务面）。
    返回 (rc, stdout, stderr)：卡层拒=1（tools-reject 已落账）；guard 拒=1
    （guard-reject 由 guard 落账）；环境不可用=2。spawn 注入位=单测委托面。
    """
    card = tool_cards.get_card(name)
    argv = ([card.binary] + [str(a) for a in args]) if card else [str(name)]
    ok, why = card_gate(goal_dir, name, args, ts, state_path=state_path,
                        lock_path=lock_path, pub=pub)
    if not ok:
        try:
            _append_tl(goal_dir, ts, _reject_event(name, why))
        except Exception:  # noqa: BLE001 —— 落账失败不洗白拒绝（拒绝优先返回）
            pass
        return 1, "", why + chr(10)
    runner = spawn or _guard_spawn
    guard_argv = [_sys_exe(), _guard_entry(), "exec",
                  "--goal-dir", goal_dir, "--timestamp=" + ts, "--"] + argv
    try:
        rc, out, err = runner(guard_argv)
    except FileNotFoundError as e:
        return 2, "", "guard 通道不可达: %s" % e
    if rc == 0:
        rev = card.revert if card.has_revert_obligation else ""
        try:
            _append_tl(goal_dir, ts,
                       "tool-card-exec name=%s rc=0 tier=%s rate=%s"
                       % (card.name, card.tier, card.rate), revert=rev)
        except Exception:  # noqa: BLE001 —— 落账失败不抹杀执行结果
            pass
    return rc, out, err
