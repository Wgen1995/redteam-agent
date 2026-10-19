# -*- coding: utf-8 -*-
"""说话开仗(P0 T6 件A)——POST /api/chat/say + POST /api/chat/confirm。

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
    "你是 GraphLed 红队指挥台的意图解析器。从操作员的一句话里提取开仗意图,"
    "只输出一个 JSON 对象,不要输出任何其他文字(含代码围栏)。字段:"
    '\n- action: "ignite"(要对目标开仗/扫描/渗透测试)或 "chat"(闲聊/提问/'
    '与开仗无关)\n'
    '- target: 目标(域名/IP/系统名);chat 或真提取不出→空串\n'
    '- scope: 字符串数组,作战范围描述(如 ["*.example.com","只读探测"]);'
    "没有→空数组\n"
    '- budget_note: 预算/时限描述(尽量带原话数字,如 "50万 tokens,4 小时");'
    "没有→空串\n"
    "- questions: 还缺的关键信息问题数组。你能从话里合理推断的一律不问,"
    "真缺才问(典型: 没提预算→问预算;目标明确就别问目标);无缺→空数组")


_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*|```\s*$")


def parse_intent(user_text):
    """LLM 意图解析 → {action,target,scope,budget_note,questions};
    链败/回非 JSON → {"error":…}(不猜不造假)。"""
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
    if not isinstance(doc, dict) or doc.get("action") not in ("ignite", "chat"):
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
