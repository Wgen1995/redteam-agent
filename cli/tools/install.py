# -*- coding: utf-8 -*-
"""装卡验签+在役清单（W3③）。

装卡=三重核通过后入在役册（roster）：①卡在注册表 ②tools.lock 验签+内容
摘要匹配 ③写入 state 行（name/version/sha256/时戳）。执行入口的供应链门=
在役行 sha 鲜度 + lock 现场复验（gate.py），「装过」不豁免「每次执行复验」。

state 路径解析序：显式参 > TANYIN_TOOLS_STATE env > ~/.tanyin/tools-installed.tsv
（不落仓内——运行时状态与仓内容分离，selfcheck layout 同律）。
"""
import os

from . import cards as tool_cards
from . import lock as tool_lock

_STATE_FIELDS = ("name", "version", "sha256", "ts")
_HOME_STATE = os.path.join(os.path.expanduser("~"), ".tanyin",
                           "tools-installed.tsv")
TAB = chr(9)
LF = chr(10)


def default_state_path():
    return os.environ.get("TANYIN_TOOLS_STATE") or _HOME_STATE


def load_state(path=None):
    path = path or default_state_path()
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip(LF)
            if not ln.strip() or ln.startswith("#"):
                continue
            parts = ln.split(TAB)
            if len(parts) != 4:
                continue  # 容忍脏行（在役册=运行态非账本；鲜度由 sha 判）
            rows.append(dict(zip(_STATE_FIELDS, parts)))
    return rows


def _append_row(path, card, ts):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8", newline=LF) as f:
        f.write(TAB.join([card.name, card.version,
                           tool_lock.card_digest(card), ts]) + LF)


def install(name, ts, state_path=None, lock_path=None, pub=None):
    """装卡：未注册=unknown-tool 拒；验签不过拒；同摘要幂等（不重复入册）。"""
    card = tool_cards.get_card(name)
    if card is None:
        return False, "unknown-tool: %s 不在注册表（25 卡清单外拒装）" % name
    ok, why = tool_lock.verify_card(card, lock_path, pub)
    if not ok:
        return False, "装卡验签失败（不装）: %s" % why
    sp = state_path or default_state_path()
    digest = tool_lock.card_digest(card)
    if any(r["name"] == card.name and r["sha256"] == digest
           for r in load_state(sp)):
        return True, "已在役（同摘要幂等）: %s" % card.name
    _append_row(sp, card, ts)
    return True, "装卡入役: %s@%s" % (card.name, card.version)


def is_installed(card, state_path=None):
    """在役判定=该卡最新行 sha==当前卡摘要（漂移即过期，复原即有效）。"""
    if card is None:
        return False
    latest = None
    for r in load_state(state_path):
        if r["name"] == card.name:
            latest = r
    return bool(latest) and latest["sha256"] == tool_lock.card_digest(card)


def uninstall(name, state_path=None):
    """除役：重写在役册剔除该卡全部行（供应链 revoke 面）。"""
    sp = state_path or default_state_path()
    rows = [r for r in load_state(sp) if r["name"] != name]
    os.makedirs(os.path.dirname(os.path.abspath(sp)) or ".", exist_ok=True)
    with open(sp, "w", encoding="utf-8", newline=LF) as f:
        for r in rows:
            f.write(TAB.join(r[k] for k in _STATE_FIELDS) + LF)
    return True
