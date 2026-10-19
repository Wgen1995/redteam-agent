# -*- coding: utf-8 -*-
"""内联审批(P0 T8 件A)——POST /api/chat/approve。

铁律对齐:
- 读面零直写: 本文件不碰 battles 根/账本文件;审批一律 subprocess 调
  engine_bridge approve(单写者执行面→tanyin-ledger approve 链)。
- 引擎零改: CLI 子命令/参数面逐字对齐 cli/ledger/write_cmds._approve
  (--command-hash/--decision/--approver/--timestamp/--note/--sig);
  键=sha256(revert_cmd),与 ledger_reader.approvals_pending 的 id 同源
  (T2 注记),未知哈希在读面就 404 不起子进程。
- 零假数: 桥失败/超时/回执与读回不一致 → 502 {"error"} 如实报,
  待审清单纹丝不动;成功才 200,且读回验证已消项+链上真有审批行。

流: {battle,command_hash,decision:"approve"|"reject",note?} →
404(未知仗/未知哈希/已决) | 422(decision 词表外) | 502(桥败) |
200 {ok,decision,approval_id,pending_left,…}。
"""
import json
import os
import subprocess
import sys

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .. import ledger_reader
from .chat import _battle_goals

router = APIRouter(prefix="/api/chat", tags=["chat"])

# engine_bridge 子进程执行面(读面唯一写出口;本模块零账本直写)。
_BRIDGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))), "engine_bridge.py")
_BRIDGE_TIMEOUT_S = 60.0

# 指挥台词汇 → 引擎词表(write_cmds._APPROVE_DECISIONS 子集:
# exempted=预授权豁免走引擎 preauth,knowledge-approved=知识审批,不在此)。
_DECISIONS = {"approve": "approved", "reject": "rejected"}


class ApproveBody(BaseModel):
    battle: str
    command_hash: str
    decision: str
    note: str = ""


def _bridge_approve(battle, command_hash, engine_decision, note):
    """engine_bridge approve 子进程 → (receipt|None, error|None)。"""
    argv = [sys.executable, _BRIDGE, "approve",
            "--battle", battle, "--command-hash", command_hash,
            "--decision", engine_decision]
    if note:
        argv += ["--note", note]
    try:
        cp = subprocess.run(argv, capture_output=True, text=True,
                            timeout=_BRIDGE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, "审批桥超时(%ss,单写者链可能在忙)——待审未动,稍后重试"             % int(_BRIDGE_TIMEOUT_S)
    receipt = None
    lines = (cp.stdout or "").strip().splitlines()
    if lines:
        try:
            receipt = json.loads(lines[-1])
        except ValueError:
            receipt = None
    if cp.returncode != 0 or not isinstance(receipt, dict)             or not receipt.get("ok"):
        return receipt, "审批桥失败(rc=%d): %s" % (
            cp.returncode,
            ((cp.stdout or "") + (cp.stderr or "")).strip()[:200])
    return receipt, None


@router.post("/approve")
def chat_approve(body: ApproveBody):
    engine_decision = _DECISIONS.get((body.decision or "").strip())
    if engine_decision is None:
        return JSONResponse(status_code=422, content={
            "error": "decision 须 approve|reject: %r" % (body.decision,)})
    battle = (body.battle or "").strip()
    goal = next(((b, gd) for b, gd in _battle_goals(None) if b == battle), None)
    if goal is None:
        return JSONResponse(status_code=404, content={
            "error": "battle 不存在(或无 goal 代目录): %r" % battle})
    _battle, goal_dir = goal
    command_hash = (body.command_hash or "").strip()
    pending = ledger_reader.approvals_pending(goal_dir)
    item = next((it for it in pending if it["id"] == command_hash), None)
    if item is None:
        return JSONResponse(status_code=404, content={
            "error": "command_hash 不在待审队列(可能已决/已核销/换代): %s"
                     % command_hash,
            "battle": battle, "pending": len(pending)})
    receipt, error = _bridge_approve(battle, command_hash, engine_decision,
                                     (body.note or "").strip())
    if error is not None:
        return JSONResponse(status_code=502, content={"error": error,
                                                      "bridge": receipt})
    # 读回验证(零假数): 待审消项+链上真有该决定行,不一致如实报 502。
    pending_after = ledger_reader.approvals_pending(goal_dir)
    if any(it["id"] == command_hash for it in pending_after):
        return JSONResponse(status_code=502, content={
            "error": "桥回执 ok 但读回待审未消项(读写不一致,如实报): %s"
                     % command_hash,
            "bridge": receipt})
    from ledger import core as ledger_core      # 列义单源(读回对照)
    from ledger.schemas import TABLES
    ap = ledger_core.Session(goal_dir).rows("approvals.tsv")
    i_hash = TABLES["approvals.tsv"].index("command_hash")
    i_dec = TABLES["approvals.tsv"].index("decision")
    if not any(r[i_hash] == command_hash and r[i_dec] == engine_decision
               for r in ap):
        return JSONResponse(status_code=502, content={
            "error": "桥回执 ok 但链上无 %s 决定行(读写不一致,如实报)"
                     % engine_decision,
            "bridge": receipt})
    return {
        "ok": True,
        "battle": battle,
        "command_hash": command_hash,
        "decision": body.decision.strip(),
        "approval_id": receipt.get("approval_id", ""),
        "event": item["event"],
        "pending_left": len(pending_after),
        "note": ("已%s,审批记录入链(%s);时刻流稍后自然见 approve 事件"
                 % ("批准" if engine_decision == "approved" else "拒绝",
                    receipt.get("approval_id", "?"))),
        "bridge": receipt,
    }
