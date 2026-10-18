# -*- coding: utf-8 -*-
"""WebShell 受控档——会话=账本行族 open→exec→close（行只增不改）。

执法链（每次执行仍入账——拒执行也留审计行）:
  open   L3 族门（c2-webshell）→意图引用闭合→URL 门（scheme http/https+
         host 非空+禁碰口 8900/3000/8787/8443）→bounds hosts 域（出界即停）;
  exec   L3 族门→会话开档校验→guard deny（ledger.enforce.deny_forms 单源
         副作用黑名单,shell 包装逃逸同检）→命中=审计行+拒执行;
         副作用必带 revert_cmd（义务律: 无回滚不入账）→reverts.tsv 登记
         pending 义务,revert_id 锚进 exec 行;
  close  L3 族门→义务未清不得关档（fail-closed）→close 行。
"""
import re
import shlex
import urllib.parse

from ..ledger import core as ledger_core
from ..ledger import enforce
from . import families
from .store import C2Error, C2Store
from .tables import PORT_DENYLIST, cols

_VAULT_RE = re.compile(r"^\{\{vault:cred-\d+\}\}$")
_DEFAULT_PORT = {"http": 80, "https": 443}


def _ci(table="webshells.tsv"):
    return {k: i for i, k in enumerate(cols(table))}


def _intent_exists(goal_dir, intent_ref):
    s = ledger_core.Session(goal_dir)
    return intent_ref in {r[0] for r in s.rows("intents.tsv")}


def _check_cred(goal_dir, cred_ref):
    if not cred_ref:
        return
    s = ledger_core.Session(goal_dir)
    ids = {r[0] for r in s.rows("creds.tsv")}
    if cred_ref not in ids and not _VAULT_RE.match(cred_ref):
        raise C2Error(
            "cred_ref 非法: %r（怎么走: creds.tsv 在册 CRED id 或 {{vault:cred-N}} 占位符,"
            "凭据真值只进 vault）" % cred_ref)


def open_session(goal_dir, ts, url, intent_ref, cred_ref="", note=""):
    """开 WebShell 受控档;返回 (WSH id, open 行)。

    fail-closed 门序: 族门→意图闭合→凭据形→URL 门→禁碰口→bounds hosts。
    """
    fam = families.require(goal_dir, "c2-webshell", ts)
    if not _intent_exists(goal_dir, intent_ref):
        raise C2Error(
            "intent_ref 引用闭合失败: %s（怎么走: 先 add-intent 登记来源意图）" % intent_ref)
    _check_cred(goal_dir, cred_ref)
    parts = urllib.parse.urlsplit(str(url))
    if parts.scheme not in _DEFAULT_PORT:
        raise C2Error("URL scheme 非法: %s（怎么走: 受控档仅 http/https）" % parts.scheme)
    host = (parts.hostname or "").lower()
    if not host:
        raise C2Error("URL host 空: %r（怎么走: 给出回环靶完整 URL）" % url)
    try:
        port = parts.port
    except ValueError:
        raise C2Error("URL port 非数字: %r" % url)
    port = port or _DEFAULT_PORT[parts.scheme]
    if port in PORT_DENYLIST:
        raise C2Error(
            "禁碰口 %d（ZhuLong 8900/控制台 3000/egress 8787/8443——C2 动态口执法,命中即拒;"
            "怎么走: 换非保留口）" % port)
    b = families.bounds_of_row(fam)
    if "hosts" in b and host not in b["hosts"]:
        raise C2Error("bounds hosts 出界: %s 不在 %s（出界即停——重新授批扩域或换域内靶）"
                      % (host, ",".join(b["hosts"])))
    store = C2Store(goal_dir)
    sid = store.next_id("webshells.tsv", "WSH")
    row = store.append("webshells.tsv", {
        "id": sid, "kind": "open", "ts": ts, "url": str(url),
        "intent_ref": intent_ref, "cred_ref": cred_ref, "cmd": "",
        "deny_check": "pass:port=%d" % port, "revert_id": "", "note": note})
    return sid, row


def _deny_hit(cmd):
    """guard deny 单源比对: enforce.deny_forms 全形过 deny_hit。"""
    argv = shlex.split(cmd) if isinstance(cmd, str) else [str(a) for a in cmd]
    if not argv or not " ".join(argv).strip():
        raise C2Error("命令载荷空（空指令不入账）")
    for form in enforce.deny_forms(argv):
        hit = enforce.deny_hit(form)
        if hit:
            return argv, hit
    return argv, None


def _live_session(store, session_id):
    ci = _ci()
    fam = store.latest_by_key("webshells.tsv")
    if session_id not in fam:
        raise C2Error("未知 WebShell 会话: %s（怎么走: 先 open_session 开档）" % session_id)
    if fam[session_id][ci["kind"]] == "close":
        raise C2Error("会话已关档: %s（受控档只增——重开=新会话 id）" % session_id)
    return fam[session_id]


def exec_cmd(goal_dir, session_id, cmd, ts, side_effect="", revert_cmd="", note=""):
    """受控执行一条命令;返回 dict（deny_check/revert_id/row）。

    guard deny 命中=审计行+拒执行（C2Error）;副作用无 revert_cmd=拒收。
    """
    families.require(goal_dir, "c2-webshell", ts)
    store = C2Store(goal_dir)
    _live_session(store, session_id)
    argv, hit = _deny_hit(cmd)
    cmd_str = cmd if isinstance(cmd, str) else " ".join(argv)
    if hit:
        store.append("webshells.tsv", {
            "id": session_id, "kind": "exec", "ts": ts, "url": "",
            "intent_ref": "", "cred_ref": "", "cmd": cmd_str,
            "deny_check": "deny:%s" % hit, "revert_id": "", "note": note})
        raise C2Error(
            "guard deny 命中: %s（副作用黑名单——打穿别打塌;怎么走: 换不破坏可用性的取证命令）" % hit)
    revert_id = ""
    if side_effect:
        if not str(revert_cmd).strip():
            raise C2Error(
                "副作用必带 revert 义务: %r（怎么走: 给出 revert_cmd,或不声明副作用）" % side_effect)
        revert_id = store.next_id("reverts.tsv", "RVT")
        store.append("reverts.tsv", {
            "id": revert_id, "source": "webshell", "source_id": session_id,
            "side_effect": str(side_effect), "revert_cmd": str(revert_cmd),
            "status": "pending", "ts": ts})
    row = store.append("webshells.tsv", {
        "id": session_id, "kind": "exec", "ts": ts, "url": "",
        "intent_ref": "", "cred_ref": "", "cmd": cmd_str,
        "deny_check": "pass", "revert_id": revert_id, "note": note})
    return {"session_id": session_id, "cmd": cmd_str, "deny_check": "pass",
            "revert_id": revert_id, "row": row}


def obligations(goal_dir, session_id=None):
    """未清 revert 义务投影（reverts.tsv 同 id 最新行胜,pending 才在册）。"""
    rci = _ci("reverts.tsv")
    out = []
    for r in C2Store(goal_dir).latest_by_key("reverts.tsv").values():
        if r[rci["status"]] != "pending":
            continue
        if session_id is not None and r[rci["source_id"]] != session_id:
            continue
        out.append({"id": r[rci["id"]], "source": r[rci["source"]],
                    "source_id": r[rci["source_id"]],
                    "side_effect": r[rci["side_effect"]],
                    "revert_cmd": r[rci["revert_cmd"]], "status": "pending"})
    return out


def settle_revert(goal_dir, revert_id, ts):
    """履约: 同 id 追加 status=done 行（投影即清）;未知/已清=C2Error。"""
    rci = _ci("reverts.tsv")
    row = C2Store(goal_dir).latest_by_key("reverts.tsv").get(revert_id)
    if row is None:
        raise C2Error("未知 revert 义务: %s" % revert_id)
    if row[rci["status"]] != "pending":
        raise C2Error("义务已清: %s status=%s" % (revert_id, row[rci["status"]]))
    return C2Store(goal_dir).append("reverts.tsv", {
        "id": revert_id, "source": row[rci["source"]],
        "source_id": row[rci["source_id"]], "side_effect": row[rci["side_effect"]],
        "revert_cmd": row[rci["revert_cmd"]], "status": "done", "ts": ts})


def close_session(goal_dir, session_id, ts, note=""):
    """关档: 义务未清不得关（fail-closed）;返回 close 行。"""
    families.require(goal_dir, "c2-webshell", ts)
    store = C2Store(goal_dir)
    _live_session(store, session_id)
    pend = obligations(goal_dir, session_id)
    if pend:
        raise C2Error(
            "revert 义务未清 %d 条（怎么走: settle_revert 履约后再关档——受控档不欠账离场）"
            % len(pend))
    return store.append("webshells.tsv", {
        "id": session_id, "kind": "close", "ts": ts, "url": "",
        "intent_ref": "", "cred_ref": "", "cmd": "", "deny_check": "pass",
        "revert_id": "", "note": note})


def sessions(goal_dir):
    """会话投影（读面）: [{id,url,state,execs,denies,open_reverts}]。"""
    ci = _ci()
    fam = {}
    for r in C2Store(goal_dir).read("webshells.tsv"):
        fam.setdefault(r[0], []).append(r)
    out = []
    for sid in sorted(fam):
        rows = fam[sid]
        out.append({
            "id": sid, "url": rows[0][ci["url"]],
            "state": "closed" if rows[-1][ci["kind"]] == "close" else "open",
            "execs": sum(1 for r in rows if r[ci["kind"]] == "exec"
                         and r[ci["deny_check"]] == "pass"),
            "denies": sum(1 for r in rows
                          if r[ci["deny_check"]].startswith("deny:")),
            "open_reverts": len(obligations(goal_dir, sid))})
    return out
