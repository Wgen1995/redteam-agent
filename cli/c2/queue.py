# -*- coding: utf-8 -*-
"""指令队列——指令=append-only 行，beacon 拉取=行号游标。

行律：
  cmds.tsv  指令行（id/beacon_id/argv/enqueued_at/approval_ref）——只增不改，
            行号=物理行序（append-only 下恒稳定=游标域）；
  pulls.tsv 拉取游标行（beacon_id/cursor/ts）——每次拉取追加一行，
            同 beacon 最新行胜=当前游标。

游标语义（防重发防漏发）：
  pull(beacon) = 取行号>cursor 且 beacon_id 匹配的指令 + 游标前移到
  全表尾行号（跳过他 beacon 指令——不重发；此后新指令行号必>新游标——不漏发）。
  幂等重拉=空集（游标已前移）。

执法：enqueue 要求 beacon 在册（引用闭合）；审批执法在 cli 层族门统一过
（approval_ref 列留审批锚——哪一族放的行可回溯）。
"""
from .store import C2Error, C2Store


def enqueue(goal_dir, beacon_id, argv, ts, approval_ref="", note=""):
    """指令入队（append-only 行）；beacon 不在册=拒收。返回 (cmd_id, rowno)。

    L3 族挂接：approval_ref 空=自动锚 c2-cmd 活跃族行；非空=须为该族 ts 时刻
    活跃授批行（fail-closed）。族 bounds 声明 max-cmds 时按全表现量执法——
    出界即停。
    """
    from . import families
    store = C2Store(goal_dir)
    if beacon_id not in store.latest_by_key("beacons.tsv"):
        raise C2Error(
            "beacon 不在册: %s（怎么走: 先 beacon-register 登记 beacon 再入队指令）" % beacon_id)
    if not argv or not str(argv).strip():
        raise C2Error("指令载荷空（argv 必填——空指令不入账）")
    if approval_ref:
        fam_row = families.assert_ref(goal_dir, approval_ref, "c2-cmd", ts)
    else:
        fam_row = families.require(goal_dir, "c2-cmd", ts)
        approval_ref = fam_row[0]
    b = families.bounds_of_row(fam_row)
    if "max-cmds" in b and len(store.read("cmds.tsv")) >= b["max-cmds"]:
        raise C2Error("出界即停: c2-cmd 族 max-cmds=%d 已满（怎么走: 重新授批扩量族）"
                      % b["max-cmds"])
    cid = store.next_id("cmds.tsv", "CMD")
    store.append("cmds.tsv", {
        "id": cid, "beacon_id": beacon_id, "argv": " ".join(str(a) for a in argv)
        if isinstance(argv, (list, tuple)) else str(argv),
        "enqueued_at": ts, "approval_ref": approval_ref, "note": note})
    rowno = len(store.read("cmds.tsv"))
    return cid, rowno


def cursor_of(goal_dir, beacon_id):
    """beacon 当前游标（pulls.tsv 同 beacon 最新行胜；无拉取史=0）。"""
    store = C2Store(goal_dir)
    cur = 0
    for r in store.read("pulls.tsv"):
        if r[1] == beacon_id:
            cur = max(cur, int(r[2]))
    return cur


def pending(goal_dir, beacon_id):
    """待拉指令（行号>游标 且 beacon_id 匹配）——只读面，不动游标。"""
    store = C2Store(goal_dir)
    cur = cursor_of(goal_dir, beacon_id)
    out = []
    for rowno, r in store.read_numbered("cmds.tsv"):
        if rowno > cur and r[1] == beacon_id:
            out.append({"rowno": rowno, "id": r[0], "argv": r[2],
                        "enqueued_at": r[3], "approval_ref": r[4]})
    return out


def pull(goal_dir, beacon_id, ts):
    """beacon 拉取：返回待拉指令并追加游标行（游标=全表现尾行号）。

    返回 (cmds, new_cursor)。幂等：无新指令=空集+游标不动（尾行号未增）。
    """
    store = C2Store(goal_dir)
    cmds = pending(goal_dir, beacon_id)
    rows = store.read("cmds.tsv")
    new_cursor = len(rows)
    if cmds:
        store.append("pulls.tsv", {
            "id": store.next_id("pulls.tsv", "PULL"), "beacon_id": beacon_id,
            "cursor": new_cursor, "ts": ts})
    return cmds, new_cursor
