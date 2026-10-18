# -*- coding: utf-8 -*-
"""L3 预授权审批族——gates-speed 预授权档: 批一次放一族,每次执行仍入账。

行律（families.tsv,行族投影同 id 最新行胜）:
  grant 行   授批: family ∈ FAMILIES 在册面;bounds 键 ∈ {hosts,max-cmds}
              （出界即停的执法面——拼写漂移 fail-closed）;valid_until>valid_from;
  revoke 行  撤批: 同 id 追加 decision=revoke（不改历史行）——投影即死。

窗口语义: valid_from <= ts <= valid_until（含端点;ISO8601 Z 字典序同律
_add_goal 授权窗口）;出窗=族死（fail-closed,怎么走=重新授批）。

挂接面（C2 面每次执行仍入账=调用方 append 的行即入账）:
  c2-beacon→beacon.register / c2-cmd→queue.enqueue（approval_ref 锚族行）/
  c2-echo→echo.submit / c2-webshell→webshell.open/exec/close。
"""
from .store import C2Error, C2Store
from .tables import FAMILIES

_BOUNDS_KEYS = ("hosts", "max-cmds")
_CI = None


def _ci():
    global _CI
    if _CI is None:
        from .tables import cols
        _CI = {k: i for i, k in enumerate(cols("families.tsv"))}
    return _CI


def parse_bounds(bounds):
    """bounds 声明域 -> dict;空=无界;malformed/越册键=C2Error（fail-closed）。

    形: "hosts=127.0.0.1,::1;max-cmds=5"（分号段,key=value）。
    """
    if not bounds:
        return {}
    out = {}
    for part in str(bounds).split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise C2Error("bounds 段非法（须 key=value）: %r" % part)
        k, v = part.split("=", 1)
        if k not in _BOUNDS_KEYS:
            raise C2Error("bounds 键越册: %r（在册: %s）——出界即停先于拼写漂移"
                          % (k, " ".join(_BOUNDS_KEYS)))
        if k == "max-cmds":
            if not v.strip().isdigit() or int(v.strip()) < 1:
                raise C2Error("bounds max-cmds 须正整数: %r" % v)
            out[k] = int(v.strip())
        else:
            hosts = [h.strip().lower() for h in v.split(",") if h.strip()]
            if not hosts:
                raise C2Error("bounds hosts 空清单非法: %r" % v)
            out[k] = hosts
    return out


def bounds_of_row(row):
    """族行的 bounds 字段 -> dict（读面投影用）。"""
    return parse_bounds(row[_ci()["bounds"]])


def grant(goal_dir, family, bounds, approver, valid_from, valid_until, ts, note=""):
    """授批一个族;返回 (FAM id, 行)。越册族/坏窗口/坏 bounds=C2Error。"""
    if family not in FAMILIES:
        raise C2Error("族越册: %s（在册: %s）——预授权族按 FAMILIES 清单收口"
                      % (family, " ".join(FAMILIES)))
    parse_bounds(bounds)
    if not str(approver).strip():
        raise C2Error("approver 空（批必有主——匿名授批不入账）")
    if not valid_until > valid_from:
        raise C2Error("族窗口非法: valid_until<=valid_from（%s..%s）" % (valid_from, valid_until))
    store = C2Store(goal_dir)
    fid = store.next_id("families.tsv", "FAM")
    row = store.append("families.tsv", {
        "id": fid, "family": family, "bounds": bounds, "decision": "grant",
        "approver": approver, "valid_from": valid_from, "valid_until": valid_until,
        "note": note, "ts": ts})
    return fid, row


def _latest_rows(store):
    """同 id 最新行胜,保持文件序（撤批行顶掉授批行的投影位）。"""
    rows = store.read("families.tsv")
    latest = {}
    for r in rows:
        latest[r[0]] = r
    return [r for r in rows if latest[r[0]] is r]


def active(goal_dir, family, ts):
    """ts 时刻该族的活跃授批行（最新授批胜）;无=None。"""
    ci = _ci()
    hit = None
    for r in _latest_rows(C2Store(goal_dir)):
        if r[ci["family"]] != family or r[ci["decision"]] != "grant":
            continue
        if not (r[ci["valid_from"]] <= ts <= r[ci["valid_until"]]):
            continue
        hit = r
    return hit


def require(goal_dir, family, ts):
    """族门（fail-closed）: 活跃行 or C2Error。返回族行（[0]=FAM id）。"""
    row = active(goal_dir, family, ts)
    if row is None:
        raise C2Error(
            "L3 预授权族未放行: %s @%s（未批/已撤/出窗;怎么走: families-grant 放行后再执行——"
            "批一次放一族,出界即停）" % (family, ts))
    return row


def ref_row(goal_dir, fam_id):
    """该 FAM id 的最新行（行族投影）;无=None。"""
    return C2Store(goal_dir).latest_by_key("families.tsv").get(fam_id)


def assert_ref(goal_dir, fam_id, family, ts):
    """审批锚校验: fam_id 须=该族 ts 时刻的活跃授批行;否则 C2Error。"""
    row = ref_row(goal_dir, fam_id)
    ci = _ci()
    if row is None or row[ci["decision"]] != "grant" or row[ci["family"]] != family:
        raise C2Error("审批锚非法: %s 非 %s 族的授批行（怎么走: 留空自动锚活族,或给 FAM id）"
                      % (fam_id, family))
    if not (row[ci["valid_from"]] <= ts <= row[ci["valid_until"]]):
        raise C2Error("审批锚出窗: %s @%s（怎么走: 重新授批）" % (fam_id, ts))
    return row


def revoke(goal_dir, fam_id, ts, note=""):
    """撤批: 同 id 追加 revoke 行（投影即死,不改历史）;未知 id=C2Error。"""
    ci = _ci()
    row = ref_row(goal_dir, fam_id)
    if row is None:
        raise C2Error("未知族行: %s（怎么走: 先 grant 产生 FAM id）" % fam_id)
    return C2Store(goal_dir).append("families.tsv", {
        "id": fam_id, "family": row[ci["family"]], "bounds": row[ci["bounds"]],
        "decision": "revoke", "approver": row[ci["approver"]],
        "valid_from": row[ci["valid_from"]], "valid_until": row[ci["valid_until"]],
        "note": note, "ts": ts})
