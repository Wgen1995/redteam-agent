# -*- coding: utf-8 -*-
"""T12 发现页读面+复验触发(engine_bridge 子进程,读面零直写)。

- 列表/过滤/详情=chat.findings_doc 单源复用(T9 同律),零第二份列义;
- 详情证据袋明细=E-index.tsv 引用行(latest_by 同源)+复放判定史
  (replay/<EV>/<seq>.json 判定产物,引擎 tanyin-replay 只增不覆盖);
- 复验=bridge reverify → tanyin-replay 真重放(治理四门内建),判定如实
  回报;状态回写走验证官 settle 门,本端不代写(set-replay-state 是验证
  官的写面,指挥台不伪造判定)。
"""
import json
import os
import subprocess
import sys
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .. import ledger_reader
from .chat import _battle_goals, findings_doc

router = APIRouter(prefix="/api/findings", tags=["findings"])

_BRIDGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "engine_bridge.py")


@router.get("")
def list_findings(battle: Optional[str] = None,
                  severity: Optional[str] = None,
                  state: Optional[str] = None):
    """发现清单(battle 可空=全仗)+severity/state 过滤,纯读零副作用。"""
    rows = findings_doc(None, battle=battle)
    if severity:
        rows = [r for r in rows if r["severity"] == severity]
    if state == "verified":
        rows = [r for r in rows if r["verified"]]
    elif state == "pending":
        rows = [r for r in rows if not r["verified"]]
    elif state:
        rows = []
    return rows


def _locate(fid):
    for row in findings_doc(None):
        if row["id"] == fid:
            return row
    return None


@router.get("/{fid}")
def finding_detail(fid: str):
    row = _locate(fid)
    if row is None:
        return JSONResponse(status_code=404, content={"error": "未知发现: %s" % fid})
    gd = dict(_battle_goals(None)).get(row["battle"])
    ev_detail, replay_hist = [], []
    if gd:
        s = ledger_reader.ledger_core.Session(gd)
        e = ledger_reader.TABLES["E-index.tsv"]
        rows = {r[0]: r for r in s.rows("E-index.tsv")}
        for ev in row["evidence"]:
            r = rows.get(ev)
            if r is None:
                ev_detail.append({"id": ev, "missing": True})
                continue
            def _col(name):
                try:
                    return r[e.index(name)]
                except (ValueError, IndexError):
                    return ""
            ev_detail.append({"id": ev, "kind": _col("kind"),
                              "created": _col("created"),
                              "card_path": _col("card_path")})
            d = os.path.join(gd, "replay", ev)
            if os.path.isdir(d):
                seqs = sorted((f for f in os.listdir(d) if f.endswith(".json")),
                              key=lambda f: int(f.split(".")[0]))
                for fn in seqs:
                    try:
                        doc = json.load(open(os.path.join(d, fn), encoding="utf-8"))
                    except (ValueError, OSError):
                        continue
                    replay_hist.append({"ev": ev, "seq": int(fn.split(".")[0]),
                                        "verdict": doc.get("verdict")})
    out = dict(row)
    out["evidence_detail"] = ev_detail
    out["replay_history"] = replay_hist
    return out


def _bridge_reverify(battle, fid):
    """子进程调桥(写面单源;TANYIN_HOME 随环境透传)。"""
    return subprocess.run(
        [sys.executable, _BRIDGE, "reverify", "--battle", battle,
         "--finding", fid],
        capture_output=True, text=True, timeout=300)


@router.post("/{fid}/reverify")
def finding_reverify(fid: str):
    row = _locate(fid)
    if row is None:
        return JSONResponse(status_code=404, content={"error": "未知发现: %s" % fid})
    if not row["evidence"]:
        return JSONResponse(status_code=422, content={
            "error": "该发现无绑定证据卡,无可复放(灰卡待验证官绑定 EV)"})
    try:
        p = _bridge_reverify(row["battle"], fid)
    except Exception as e:                     # noqa: BLE001 如实不造假
        return JSONResponse(status_code=502, content={
            "error": "复验桥调用失败: %s" % e})
    doc = None
    for ln in reversed((p.stdout or "").splitlines()):
        if ln.strip().startswith("{"):
            try:
                doc = json.loads(ln)
                break
            except ValueError:
                continue
    if p.returncode != 0 or not doc or not doc.get("ok"):
        return JSONResponse(status_code=502, content={
            "error": "复验失败(桥 rc=%d): %s"
                     % (p.returncode, (doc or {}).get("error")
                        or (p.stderr or "")[-200:])})
    return doc
