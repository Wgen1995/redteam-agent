# -*- coding: utf-8 -*-
"""说话开仗(P0 T6 件A + T10 插话转向)——POST /api/chat/say + /confirm
+ GET /api/chat/running + POST /api/chat/steer + POST /api/chat/halt。

铁律对齐:
- 读面零直写: 本文件不碰 battles 根/账本文件;确认点火一律 subprocess
  调 engine_bridge(单写者执行面),拒绝=零子进程零写入只播报。
- 引擎零改: LLM 意图解析走 ~/.tanyin/channels.json 双钥链,协议同引擎
  warrior/model_client 同族(openai 兼容 /chat/completions,temperature=0,
  ProxyHandler({}) 绕环境代理)——读面自带轻客户端,不 import 引擎战士模块。
- 零假数: LLM 链全败→502 {"error"} 不造意图不造卡;LLM 回非 JSON 同拒。

流(三型):
1. say{text} → 意图 {action,target,scope,budget_note,questions};
2. action=ignite 且无缺问 → 确认卡 {kind:"confirm-ignite",…} 暂存
   (session 级 dict)→ {status:"confirm",card};有缺问 → {status:"ask"};
   action=chat → {status:"chat,reply}(闲聊直回,不点火);
3. confirm{id,approved}: 批→engine_bridge ignite --dry-run(P0 一律
   dry-run,真点火后续舰);拒→{cancelled:true,note:"已取消,目标保留"}。
T10 扩:
4. 意图三分类扩 action="steer"|"halt"(仗在跑时对进行中仗的指令——跳过某
   目标/重点某处/停;带 target_intent 线索)→say 只分类+指路(不猜仗标),
   {status:"steer"|"halt",intent:{target_intent}};
5. GET /api/chat/running: 在跑仗条数据面(执行中口径=tasks_view「执行中」
   单源+badge 同 stream 派生),无在跑=空不造假;
6. POST /api/chat/steer{battle,text,intent?}: 桥 steer 逐战士铸
   warrior-steer 行(cli/warrior/steer.py 单源写面,原文必达);
   POST /api/chat/halt{battle,reason?}: 桥 halt 铸 warrior-stop(逐战士)
   +deck-halt 留痕。未知仗 404/缺参 422/桥败或读写不一致 502 不造假;
   回执时刻卡经流轮询自然来,本文件零伪造。
"""
import json
import os
import re
import secrets
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 导入序: ledger_reader 导入即把仓根 cli/ 前上 sys.path,ledger/webui 随后可导
# (approvals.py 同先例);chat._badge/_battle_goals 与 overview._RUNNING_LABEL
# =徽标/执行中口径单源复用,零第二份。
from .. import ledger_reader
from .chat import _badge, _battle_goals
from .overview import _RUNNING_LABEL
from ledger.session_view import default_battles_dir
from webui import api_v2_tasks

router = APIRouter(prefix="/api/chat", tags=["chat"])

# engine_bridge 子进程执行面(读面唯一写出口;本模块零账本直写)。
_BRIDGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))), "engine_bridge.py")

# ---- 轻 LLM 客户端(引擎 model_client 同族协议;链=channels.json 序) ----

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
_CHANNELS_PATH = os.path.join(
    os.path.expanduser(os.environ.get("TANYIN_HOME", "~/.tanyin")),
    "channels.json")
_LLM_TIMEOUT_S = 60.0
_MAX_TOKENS = 1024


def _load_channels():
    """~/.tanyin/channels.json → [{name,model,base_url,api_key}](缺=[])。"""
    try:
        with open(_CHANNELS_PATH, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return []
    if not isinstance(doc, list):
        return []
    return [c for c in doc
            if isinstance(c, dict) and c.get("name")
            and c.get("base_url") and c.get("api_key")]


def _post_channel(channel, messages, timeout=_LLM_TIMEOUT_S):
    """单钥真调(openai chat completions;返回原始 body 文本,失败外抛)。"""
    payload = json.dumps({
        "model": channel.get("model", channel["name"]),
        "messages": messages,
        "temperature": 0,
        "max_tokens": _MAX_TOKENS,
    }).encode("utf-8")
    base = (channel.get("base_url") or "").rstrip("/")
    url = base if base.endswith("/chat/completions") \
        else base + "/chat/completions"
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={"Content-Type": "application/json",
                 "Accept": "application/json",
                 "Authorization": "Bearer " + channel.get("api_key", "")})
    resp = _OPENER.open(req, timeout=timeout)
    try:
        return resp.read()
    finally:
        resp.close()


def _parse_content(body):
    """openai 信封 → content str;结构不符 ValueError。"""
    doc = json.loads(body.decode("utf-8"))
    choices = doc.get("choices") if isinstance(doc, dict) else None
    if not isinstance(choices, list) or not choices:
        raise ValueError("no choices")
    choice = choices[0]
    content = (choice.get("message") or {}).get("content") \
        if isinstance(choice, dict) else None
    if not isinstance(content, str):
        raise ValueError("content not str")
    return content


def llm_chat(messages, channels=None, timeout=_LLM_TIMEOUT_S):
    """链式逐钥: 429/401/网络错→下一钥;全败 {ok:False,attempts 留痕}。"""
    chain = channels if channels is not None else _load_channels()
    attempts = []
    for ch in chain:
        try:
            body = _post_channel(ch, messages, timeout)
        except urllib.error.HTTPError as e:
            attempts.append({"model": ch["name"],
                             "outcome": "http-%s" % getattr(e, "code", 0)})
            continue                     # 429/401/…→下一钥
        except Exception as e:           # URLError/timeout/OSError
            attempts.append({"model": ch["name"], "outcome": "network"})
            continue
        try:
            content = _parse_content(body)
        except (ValueError, UnicodeDecodeError):
            attempts.append({"model": ch["name"], "outcome": "bad-response"})
            continue
        attempts.append({"model": ch["name"], "outcome": "ok"})
        return {"ok": True, "content": content, "model": ch["name"],
                "attempts": attempts}
    return {"ok": False,
            "error": "llm-chain-exhausted(共试 %d 钥,全败)" % len(attempts),
            "attempts": attempts}


# ---- 意图解析 ----

_INTENT_SYSTEM = (
    "你是 GraphLed 红队指挥台的意图解析器。从操作员的一句话里提取意图,"
    "只输出一个 JSON 对象,不要输出任何其他文字(含代码围栏)。字段:"
    '\n- action: "ignite"(要对目标开仗/扫描/渗透测试)、"steer"(有仗在跑时,'
    "这句是对进行中仗的指令——跳过某目标/重点某处/转向/补充要求,不是开新仗)、"
    '"halt"(有仗在跑时,这句要求停掉进行中的仗——全停/先停下/别打了)、'
    '或 "chat"(闲聊/提问/与作战无关)\n'
    '- target: 目标(域名/IP/系统名);ignite 外或真提取不出→空串\n'
    '- scope: 字符串数组,作战范围描述(如 ["*.example.com","只读探测"]);'
    "没有→空数组\n"
    '- budget_note: 预算/时限描述(尽量带原话数字,如 "50万 tokens,4 小时");'
    "没有→空串\n"
    "- target_intent: 仅 steer/halt 用——指令指向的线索(如 \"跳过 10.2.0.9\"、"
    '\"重点 login.example.com\"、\"全部停\");其余 action→空串\n'
    "- questions: 还缺的关键信息问题数组。你能从话里合理推断的一律不问,"
    "真缺才问(典型: 没提预算→问预算;目标明确就别问目标);无缺→空数组")


_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*|```\s*$")


def parse_intent(user_text):
    """LLM 意图解析 → {action,target,scope,budget_note,questions,
    target_intent};链败/回非 JSON → {"error":…}(不猜不造假)。"""
    reply = llm_chat([
        {"role": "system", "content": _INTENT_SYSTEM},
        {"role": "user", "content": user_text},
    ])
    if not reply.get("ok"):
        return {"error": "模型链全败,意图解析不可用: %s(%s)" % (
            reply.get("error", ""),
            "; ".join("%s=%s" % (a["model"], a["outcome"])
                      for a in reply.get("attempts", [])))}
    raw = (reply.get("content") or "").strip()
    cleaned = _FENCE_RE.sub("", raw).strip()
    lo, hi = cleaned.find("{"), cleaned.rfind("}")
    if lo < 0 or hi <= lo:
        return {"error": "LLM 回执非 JSON 意图对象(拒猜): %s" % cleaned[:120]}
    try:
        doc = json.loads(cleaned[lo:hi + 1])
    except ValueError:
        return {"error": "LLM 回执 JSON 解析失败(拒猜): %s" % cleaned[:120]}
    if not isinstance(doc, dict) or doc.get("action") not in (
            "ignite", "chat", "steer", "halt"):
        return {"error": "LLM 回执缺合法 action(拒猜): %s" % cleaned[:120]}
    scope = doc.get("scope")
    questions = doc.get("questions")
    return {
        "action": doc["action"],
        "target": str(doc.get("target") or "").strip(),
        "scope": [str(s) for s in scope if str(s).strip()]
            if isinstance(scope, list) else [],
        "budget_note": str(doc.get("budget_note") or "").strip(),
        "questions": [str(q) for q in questions if str(q).strip()]
            if isinstance(questions, list) else [],
        "target_intent": str(doc.get("target_intent") or "").strip(),
    }


# ---- 确认卡暂存(session 级 dict;进程重启即清,属预期骨架行为) ----

_pending_cards = {}

_AUTH_NOTICE = (
    "确认开打仅按 dry-run 演练(P0);真点火须授权书在位"
    "(signer/有效期/sha256 校验)且预算上限过仲裁。")


def _make_card(intent):
    return {
        "kind": "confirm-ignite",
        "id": secrets.token_hex(8),
        "target": intent["target"],
        "scope": intent["scope"],
        "budget": intent["budget_note"],
        "auth_notice": _AUTH_NOTICE,
    }


class SayBody(BaseModel):
    text: str


class ConfirmBody(BaseModel):
    id: str
    approved: bool


@router.post("/say")
def chat_say(body: SayBody):
    text = (body.text or "").strip()
    if not text:
        return JSONResponse(status_code=422, content={"error": "text 必填"})
    intent = parse_intent(text)
    if "error" in intent:
        return JSONResponse(status_code=502, content={"error": intent["error"]})
    if intent["action"] == "chat":
        return {"status": "chat",
                "reply": "已收到。这句未识别为开仗指令——"
                         "说清目标(可选范围/预算)即可开仗。"}
    if intent["action"] in ("steer", "halt"):
        # T10 插话/停令: say 面不知仗标(零假数——不猜该插给哪仗),
        # 只分类+线索透传;发出走 /steer /halt(流顶在跑仗条带仗标)。
        word = "插话指令" if intent["action"] == "steer" else "停仗指令"
        knob = "插话" if intent["action"] == "steer" else "全停"
        clue = intent["target_intent"]
        return {"status": intent["action"],
                "reply": "已识别为对进行中仗的%s%s——请用流顶在跑仗条的"
                         "「%s」钮发出(插话/停令会带仗标直达该仗战士)。"
                         % (word, "(线索: %s)" % clue if clue else "", knob),
                "intent": {"target_intent": clue}}
    if intent["questions"]:
        return {"status": "ask", "questions": intent["questions"],
                "intent": {k: intent[k] for k in
                           ("target", "scope", "budget_note")}}
    card = _make_card(intent)
    _pending_cards[card["id"]] = card
    return {"status": "confirm", "card": card}


def _bridge_ignite(card):
    """批确认 → engine_bridge 子进程 ignite --dry-run(P0 唯一模式)。"""
    argv = [sys.executable, _BRIDGE, "ignite",
            "--target", card["target"]]
    for s in card.get("scope") or []:
        argv += ["--scope", s]
    if card.get("budget"):
        argv += ["--budget", card["budget"]]
    argv.append("--dry-run")
    cp = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    receipt = None
    out_lines = (cp.stdout or "").strip().splitlines()
    if out_lines:
        try:
            receipt = json.loads(out_lines[-1])
        except ValueError:
            receipt = None
    if cp.returncode != 0 or not isinstance(receipt, dict) \
            or not receipt.get("ok"):
        return JSONResponse(status_code=502, content={
            "error": "点火桥失败(rc=%d): %s"
                     % (cp.returncode,
                        ((cp.stdout or "") + (cp.stderr or "")).strip()[:200]),
            "bridge": receipt})
    return {
        "ok": True, "cancelled": False, "ignited": True,
        "dry_run": True, "battle": receipt.get("battle"),
        "note": "已按 dry-run 点火演练(战号 battle-%s,零落账);"
                "真点火后续舰接线" % receipt.get("battle", "?"),
        "bridge": receipt,
    }


@router.post("/confirm")
def chat_confirm(body: ConfirmBody):
    card = _pending_cards.pop(body.id, None)
    if card is None:
        return JSONResponse(status_code=404, content={
            "error": "确认卡不存在或已处理"})
    if not body.approved:
        return {"ok": True, "cancelled": True,
                "note": "已取消,目标保留(卡作废,可重新发起)"}
    return _bridge_ignite(card)


# ---------------------------------------------------------------- T10 插话转向 --

_BRIDGE_TIMEOUT_S = 60.0


def running_doc(battles_dir=None):
    """在跑仗条数据面: 执行中仗(overview 口径单源=tasks_view 界面七态
    「执行中」标签)+徽标(sha256 派生色相,stream/warboard 同源)+态说明。
    无在跑仗/根缺 → 空列表,不造数。"""
    root = battles_dir if battles_dir is not None else default_battles_dir()
    out = []
    for b in api_v2_tasks.tasks_view(battles_dir=root)["battles"]:
        if b["state"]["label"] != _RUNNING_LABEL:
            continue
        out.append({"battle": b["battle"], "badge": _badge(b["battle"]),
                    "detail": b["state"].get("detail", "")})
    return {"battles": out}


@router.get("/running")
def chat_running():
    """T10 在跑仗条: 执行中仗清单(纯读;前端 10s 轮询,无在跑=条隐藏)。"""
    return running_doc()


class SteerBody(BaseModel):
    battle: str
    text: str
    intent: str = ""


class HaltBody(BaseModel):
    battle: str
    reason: str = ""


def _run_bridge(cmd_args):
    """engine_bridge 子进程 → (receipt|None, error|None);败/超时如实报。"""
    argv = [sys.executable, _BRIDGE] + cmd_args
    try:
        cp = subprocess.run(argv, capture_output=True, text=True,
                            timeout=_BRIDGE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, "桥超时(%ss,单写者链可能在忙)——账本未动,稍后重试"
    receipt = None
    lines = (cp.stdout or "").strip().splitlines()
    if lines:
        try:
            receipt = json.loads(lines[-1])
        except ValueError:
            receipt = None
    if cp.returncode != 0 or not isinstance(receipt, dict) \
            or not receipt.get("ok"):
        return receipt, "桥失败(rc=%d): %s" % (
            cp.returncode, ((cp.stdout or "") + (cp.stderr or "")).strip()[:200])
    return receipt, None


def _tl_has_row(goal_dir, prefix, text):
    """读回验证(T8 双保险同律): 链上真有该前缀+文本(白空间折叠)的行。"""
    flat = " ".join(str(text).split())
    try:
        rows = ledger_reader.timeline_tail(goal_dir, limit=20)
    except Exception:                              # noqa: BLE001 读不回=不一致
        return False
    return any(prefix in r["detail"] and flat in r["detail"] for r in rows)


def _known_battle(battle):
    """仗名 → goal 目录|None(approvals 同律: 未知仗/无代目录 404)。"""
    hit = next(((b, gd) for b, gd in _battle_goals(None) if b == battle), None)
    return hit[1] if hit else None


@router.post("/steer")
def chat_steer(body: SteerBody):
    """插话: 输入框原文以 steer 发送(带仗标)→桥逐战士铸 warrior-steer 行。

    回执如实: 未知仗 404 / 缺 text 422 / 桥败或读写不一致 502 不造假;
    时刻卡(插话入链行)经流轮询自然来,本端点不伪造。
    """
    battle = (body.battle or "").strip()
    text = (body.text or "").strip()
    intent = (body.intent or "").strip()
    if not battle or not text:
        return JSONResponse(status_code=422, content={
            "error": "battle 与 text 必填(插话内容不可为空)"})
    goal_dir = _known_battle(battle)
    if goal_dir is None:
        return JSONResponse(status_code=404, content={
            "error": "battle 不存在(或无 goal 代目录): %r" % battle})
    argv = ["steer", "--battle", battle, "--text", text]
    if intent:
        argv += ["--intent", intent]
    receipt, error = _run_bridge(argv)
    if error is not None:
        return JSONResponse(status_code=502, content={"error": error,
                                                      "bridge": receipt})
    if not _tl_has_row(goal_dir, "warrior-steer target=", text):
        return JSONResponse(status_code=502, content={
            "error": "桥回执 ok 但链上无插话行(读写不一致,如实报)",
            "bridge": receipt})
    warriors = receipt.get("warriors") or []
    return {"ok": True, "battle": battle, "text": text, "intent": intent,
            "warriors": warriors,
            "timeline_row": receipt.get("timeline_row"),
            "note": "插话已入链(战士 %s);回执时刻经流自然来"
                    % (",".join(warriors) or "?"),
            "bridge": receipt}


@router.post("/halt")
def chat_halt(body: HaltBody):
    """全停该仗: 桥逐战士铸 warrior-stop 行+deck-halt 留痕行,在跑战士
    scan 即停。败路同 steer(404/502 如实),时刻卡经流自然来。"""
    battle = (body.battle or "").strip()
    reason = (body.reason or "").strip()
    if not battle:
        return JSONResponse(status_code=422, content={
            "error": "battle 必填(如 battle-3)"})
    goal_dir = _known_battle(battle)
    if goal_dir is None:
        return JSONResponse(status_code=404, content={
            "error": "battle 不存在(或无 goal 代目录): %r" % battle})
    argv = ["halt", "--battle", battle]
    if reason:
        argv += ["--reason", reason]
    receipt, error = _run_bridge(argv)
    if error is not None:
        return JSONResponse(status_code=502, content={"error": error,
                                                      "bridge": receipt})
    stopped = receipt.get("stopped") or []
    want_reason = reason or "指挥台全停"
    # 读回验证: 有在编战士→链上须有 warrior-stop 行;无在编→deck-halt 留痕行
    ok_readback = (_tl_has_row(goal_dir, "warrior-stop warrior=", want_reason)
                   if stopped else
                   _tl_has_row(goal_dir, "deck-halt battle=" + battle,
                               want_reason))
    if not ok_readback:
        return JSONResponse(status_code=502, content={
            "error": "桥回执 ok 但链上无停令行(读写不一致,如实报)",
            "bridge": receipt})
    return {"ok": True, "battle": battle, "reason": want_reason,
            "stopped": stopped,
            "timeline_row": receipt.get("timeline_row"),
            "note": "全停已入链(%s);停令时刻经流自然来"
                    % (",".join(stopped) if stopped else "无在编战士,仅留痕"),
            "bridge": receipt}
