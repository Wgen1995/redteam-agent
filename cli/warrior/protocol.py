# -*- coding: utf-8 -*-
"""战士指令协议（W5 战士 MVP）——模型输出 → 结构化指令流。

协议=JSON 指令块（SKILL.md 总控路由器约定的机器可解析面）：
  {"op":"tool","card":"<工具卡名>","args":[<标量>...]}      经 guard 执行
  {"op":"ledger","cmd":"<写命令>","args":{<键>:<标量>}}     经账本写命令（权面受限）
  {"op":"done","reason":"<文本>"}                           意图终报（含纯文本结论）
  {"op":"note","text":"<文本>"}                             无动作留言

容错律（VulnClaw correction_layer 同哲学：坏信号不炸循环，记错误喂下轮自纠）：
- 块提取：成对 ``` 围栏内容逐块解析；围栏外文本用 raw_decode 扫顶层 JSON 对象；
- 畸形块 → errors 行（bad-json/not-object/unknown-op/missing-field/bad-field/
  cmd-not-allowed），好块照常存活，顺序保持；
- 散文残留 → prose 单列承载（不丢、不炸、不算指令）；
- 永不 raise——解析层是循环的地板，不是门。

权面（ledger 指令 allowlist）：战士=worker（ARTEX 角色铁律：领一意图→执行→写
事实→停），只许落结果类写命令；权威命令（approve/amend-scope/set-cred-status/
set-intent-status/add-intent…）一律 cmd-not-allowed——开新方向与审批=规划者
（W5）/人的权柄。
"""
import json
import re

# 战士可执行的账本写命令（结果落账面）；其余全拒（权威面/状态面另归）
SAFE_LEDGER_CMDS = ("add-fact", "add-finding", "add-asset", "add-edge",
                    "add-evidence")

_CARD_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_SCALARS = (str, int, float)
_FENCE_RE = re.compile(r"```[a-zA-Z0-9_-]*\s*\n(.*?)```", re.DOTALL)
_MAX_ERR_RAW = 80


class ParseResult(object):
    """解析结果：instructions（合法指令 dict 列表，序=文本序）+ errors + prose。"""

    __slots__ = ("instructions", "errors", "prose")

    def __init__(self, instructions, errors, prose):
        self.instructions = instructions
        self.errors = errors
        self.prose = prose


def _err(code, raw):
    return {"error": code, "raw": str(raw)[:_MAX_ERR_RAW]}


def _is_scalar(v):
    return isinstance(v, _SCALARS) and not isinstance(v, bool)


def _check_tool(obj):
    if "card" not in obj:
        return None, _err("missing-field", "card")
    card = obj.get("card")
    if not isinstance(card, str) or not _CARD_RE.match(card):
        return None, _err("bad-field", "card: %r" % (card,))
    args = obj.get("args", [])
    if not isinstance(args, list) or not all(_is_scalar(a) for a in args):
        return None, _err("bad-field", "args 须标量列表")
    return {"op": "tool", "card": card, "args": [str(a) for a in args]}, None


def _check_ledger(obj, allowed):
    if "cmd" not in obj:
        return None, _err("missing-field", "cmd")
    cmd = obj.get("cmd")
    if not isinstance(cmd, str) or cmd not in allowed:
        return None, _err("cmd-not-allowed", cmd)
    args = obj.get("args", {})
    if not isinstance(args, dict) or not all(
            isinstance(k, str) and _is_scalar(v) for k, v in args.items()):
        return None, _err("bad-field", "args 须 str→标量 映射")
    return {"op": "ledger", "cmd": cmd,
            "args": {k: (v if isinstance(v, str) else str(v))
                     for k, v in args.items()}}, None


def _check_one(obj, allowed):
    """单对象 → (instruction|None, error|None)。op 分派+字段校验。"""
    op = obj.get("op")
    if op == "tool":
        return _check_tool(obj)
    if op == "ledger":
        return _check_ledger(obj, allowed)
    if op == "done":
        reason = obj.get("reason", "")
        if not isinstance(reason, str):
            return None, _err("bad-field", "reason 须文本")
        return {"op": "done", "reason": reason}, None
    if op == "note":
        text = obj.get("text", "")
        if not isinstance(text, str):
            return None, _err("bad-field", "text 须文本")
        return {"op": "note", "text": text}, None
    return None, _err("unknown-op", op)


def _decode_objects(text):
    """文本 → (对象列表, 非对象散文)。围栏块逐块；余文扫顶层 JSON 对象。"""
    objs, prose_parts = [], []
    fence_spans = []
    for m in _FENCE_RE.finditer(text):
        fence_spans.append((m.start(), m.end()))
        objs.append((m.group(1), True))
    prev = 0
    for s, e in fence_spans:
        prose_parts.append(text[prev:s])
        prev = e
    prose_parts.append(text[prev:])
    decoder = json.JSONDecoder()
    leftover = []
    for chunk in prose_parts:
        pos, n = 0, len(chunk)
        while pos < n:
            hits = [i for i in (chunk.find("{", pos), chunk.find("[", pos))
                    if i != -1]
            if not hits:
                leftover.append(chunk[pos:])
                break
            hit = min(hits)
            leftover.append(chunk[pos:hit])
            try:
                obj, end = decoder.raw_decode(chunk[hit:])
            except ValueError:
                leftover.append(chunk[hit])
                pos = hit + 1
                continue
            objs.append((chunk[hit:hit + end], False))
            pos = hit + end
    return objs, "".join(leftover)


def parse(text, allowed_cmds=SAFE_LEDGER_CMDS):
    """模型输出文本 → ParseResult。永不 raise（容错律见模块 docstring）。"""
    if not isinstance(text, str):
        return ParseResult([], [_err("bad-field", "content 非文本")], "")
    instructions, errors = [], []
    objs, prose = _decode_objects(text)
    for raw, fenced in objs:
        src = raw if fenced else raw
        try:
            obj = json.loads(src)
        except ValueError:
            errors.append(_err("bad-json", src))
            continue
        if not isinstance(obj, dict):
            errors.append(_err("not-object", src))
            continue
        ins, err = _check_one(obj, allowed_cmds)
        if err is not None:
            errors.append(err)
        else:
            instructions.append(ins)
    return ParseResult(instructions, errors, prose.strip())
