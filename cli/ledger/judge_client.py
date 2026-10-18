# -*- coding: utf-8 -*-
"""judge 窄调用客户端（v0.8 Task D）。

stdlib urllib 直连 openai 兼容 chat 端点（绕过环境代理）；temperature=0、
max_tokens=512、单轮。输出契约 token 级严格解析（借 ARTEX 3 路 judge 配方）：
仅接受单 JSON 对象、键白名单 verdict/comment/reason；重复键/多余字段/截断/
散文一律 verdict=None+fail reason；去代码栅栏只做确定性剥离、绝不补全截断。
fail-closed：任何网络/解析异常不外抛、不猜测，统一返回 (None, reason)。

reason 码表：
  not-configured   base_url/model/api_key 缺失（参数→env 均无）
  timeout          连接或读取超时
  network-error    网络/OS 层错误（拒绝连接等）
  http-error:CODE  非 2xx HTTP 状态
  bad-response     响应不是 openai chat 信封（无 choices/content 非 str）
  truncated        finish_reason=length（截断，绝不补全）
  duplicate-key    content JSON 出现重复键
  extra-keys       键超出白名单
  not-single-object 顶层非对象 / 多于一个 JSON 值
  prose            content 不是 JSON
  missing-verdict  对象缺 verdict 键
  unexpected-error 兜底（fail-closed 最后一道闸）
"""
import json
import logging
import os
import re
import socket
import urllib.error
import urllib.request

ENV_BASE_URL = "TANYIN_JUDGE_BASE_URL"
ENV_MODEL = "TANYIN_JUDGE_MODEL"
ENV_API_KEY = "TANYIN_JUDGE_API_KEY"

DEFAULT_TIMEOUT = 10.0
TEMPERATURE = 0
MAX_TOKENS = 512
ALLOWED_KEYS = ("verdict", "comment", "reason")

# 直连：显式绕过环境代理，保证行为确定（127.0.0.1 stub 亦不受污染）
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class _DuplicateKey(ValueError):
    """object_pairs_hook 抛出：JSON 对象出现重复键。"""


def _reject_duplicate_keys(pairs):
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise _DuplicateKey(key)
        seen.add(key)
    return dict(pairs)


def _strip_code_fence(text):
    """确定性去栅栏：仅在成对 ``` 围栏完整存在时剥离，绝不补全截断。"""
    t = text.strip()
    if t.startswith("```"):
        nl = t.find("\n")
        if nl != -1:
            body = t[nl + 1:].rstrip()
            if body.endswith("```"):
                return body[:-3].strip()
    return t


def parse_verdict(content):
    """token 级严格解析 judge 输出 -> (verdict_dict|None, reason)。"""
    text = _strip_code_fence(content)
    try:
        obj = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except _DuplicateKey:
        return None, "duplicate-key"
    except ValueError as exc:
        if "Extra data" in str(exc):
            return None, "not-single-object"  # 一个以上 JSON 值
        return None, "prose"
    if not isinstance(obj, dict):
        return None, "not-single-object"
    if set(obj) - set(ALLOWED_KEYS):
        return None, "extra-keys"
    if "verdict" not in obj:
        return None, "missing-verdict"
    return dict(obj), None


class JudgeClient(object):
    """窄调用客户端：ask(prompt) 单轮提问，无工具、无多轮。"""

    def __init__(self, base_url=None, model=None, api_key=None,
                 timeout=DEFAULT_TIMEOUT, env=None):
        env = os.environ if env is None else env
        self.base_url = base_url or env.get(ENV_BASE_URL)
        self.model = model or env.get(ENV_MODEL)
        self.api_key = api_key or env.get(ENV_API_KEY)
        self.timeout = timeout

    def _endpoint(self):
        base = (self.base_url or "").rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return base + "/chat/completions"

    def ask(self, prompt):
        """单轮提问 -> (verdict_dict|None, reason)；fail-closed 不外抛。"""
        if not (self.base_url and self.model and self.api_key):
            return None, "not-configured"
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
        }).encode("utf-8")
        req = urllib.request.Request(
            self._endpoint(), data=payload, method="POST",
            headers={"Content-Type": "application/json",
                     "Accept": "application/json",
                     "Authorization": "Bearer " + self.api_key})
        try:
            resp = _OPENER.open(req, timeout=self.timeout)
            try:
                body = resp.read()
            finally:
                resp.close()
        except urllib.error.HTTPError as exc:
            return None, "http-error:%s" % getattr(exc, "code", "?")
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, (socket.timeout, TimeoutError)):
                return None, "timeout"
            return None, "network-error"
        except (socket.timeout, TimeoutError):
            return None, "timeout"
        except OSError:
            return None, "network-error"
        except Exception:
            return None, "unexpected-error"
        try:
            return self._interpret(body)
        except Exception:
            return None, "unexpected-error"

    @staticmethod
    def _interpret(body):
        """解析 openai chat 信封；结构不符一律 bad-response。"""
        try:
            envelope = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None, "bad-response"
        if not isinstance(envelope, dict):
            return None, "bad-response"
        choices = envelope.get("choices")
        if not isinstance(choices, list) or not choices:
            return None, "bad-response"
        choice = choices[0]
        if not isinstance(choice, dict):
            return None, "bad-response"
        if choice.get("finish_reason") == "length":
            return None, "truncated"
        message = choice.get("message")
        if not isinstance(message, dict):
            return None, "bad-response"
        content = message.get("content")
        if not isinstance(content, str):
            return None, "bad-response"
        return parse_verdict(content)


def ask(prompt, base_url=None, model=None, api_key=None,
        timeout=DEFAULT_TIMEOUT, env=None):
    """独立窄接口：ask(prompt) -> (verdict_dict|None, reason)。"""
    client = JudgeClient(base_url=base_url, model=model, api_key=api_key,
                         timeout=timeout, env=env)
    return client.ask(prompt)


# ------------------------------------------------ 哨兵规则引擎（功能11补件一）
# docs/design/2026-10-20-sentinel-retest-design.md §补件一：14 类误报信号规则
# （版本化 TSV 单源 knowledge/engineering/sentinels-v1.tsv）在 findings 入库
# 路径前置跑——便宜规则先跑、贵的验证官 replay 后跑（成本序）。本段=确定性
# 纯函数（零 LLM 调用）；ask() 的 LLM 判定面与规则哨兵同宿本模块（判定引擎
# 单入口）。fail-closed 口径：规则文件缺席/头不符=空规则集放行——哨兵是前置
# 优化，验证官仍在下游，不因规则文件堵入库；单行腐（列数/枚举/regex/重复
# id）只废该行（warning 留痕），不废全库。

SENTINELS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "knowledge", "engineering", "sentinels-v1.tsv")
SENTINEL_COLUMNS = ("id", "signal_pattern", "judge", "action", "note")
SENTINEL_ACTIONS = ("downgrade-to-fact", "reject", "mark-suspicious")
# 多规则同时命中的确定性归并：从严优先（拒 > 降级 > 可疑）；同动作内按文件序。
SENTINEL_PRECEDENCE = ("reject", "downgrade-to-fact", "mark-suspicious")

_sentinel_log = logging.getLogger("tanyin.sentinels")


def load_sentinels(path=None):
    """加载版本化哨兵规则 -> (version, [rule_dict])。

    文件形：首部「# version: N」注释行 + 列头行(id/signal_pattern/judge/
    action/note) + 数据行（TSV）。加载即记版本入日志（版本可审计）。
    缺席 -> ("", []) + warning（fail-closed 放行）；列头不符 -> ("", [])。
    """
    p = path or SENTINELS_PATH
    try:
        with open(p, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError as exc:
        _sentinel_log.warning(
            "sentinel rules unavailable: %s (%s) —— fail-closed 空规则集放行", p, exc)
        return "", []
    version, rules, seen = "", [], set()
    header_seen = False
    for ln in lines:
        if not ln.strip():
            continue
        if ln.lstrip().startswith("#"):
            m = re.match(r"^#\s*version\s*:\s*(\S+)", ln)
            if m:
                version = m.group(1)
            continue
        cols = ln.split("\t")
        if not header_seen:
            if tuple(c.strip() for c in cols) != SENTINEL_COLUMNS:
                _sentinel_log.warning("sentinel 列头不符，整库拒载: %r", cols)
                return "", []
            header_seen = True
            continue
        if len(cols) != len(SENTINEL_COLUMNS):
            _sentinel_log.warning("sentinel 坏行(列数=%d)跳过: %.80s", len(cols), ln)
            continue
        rid, pattern, judge, action, note = (c.strip() for c in cols)
        if action not in SENTINEL_ACTIONS:
            _sentinel_log.warning("sentinel 坏行(action=%r)跳过: %s", action, rid)
            continue
        try:
            re.compile(pattern)
        except re.error as exc:
            _sentinel_log.warning("sentinel 坏行(regex 不编译: %s)跳过: %s", exc, rid)
            continue
        if rid in seen:
            _sentinel_log.warning("sentinel 重复 id 跳过: %s", rid)
            continue
        seen.add(rid)
        rules.append({"id": rid, "signal_pattern": pattern, "judge": judge,
                      "action": action, "note": note})
    if not version:
        _sentinel_log.warning("sentinel 规则文件缺 version 行: %s", p)
    _sentinel_log.info("sentinel rules loaded: file=%s version=%s rules=%d",
                       p, version or "?", len(rules))
    return version, rules


def run_sentinels(corpus, path=None):
    """跑全哨兵 -> {"action","rule_ids","note","version"}（同输入同判）。

    action ∈ clear|reject|downgrade-to-fact|mark-suspicious；corpus=finding
    的 title+description_brief+reproducible_steps 拼接文本；命中多条时按
    SENTINEL_PRECEDENCE 从严归并，note=胜出动作各规则 note 以「 ; 」连接。
    """
    version, rules = load_sentinels(path)
    matched = [r for r in rules
               if re.search(r["signal_pattern"], corpus or "", re.IGNORECASE)]
    action, winners = "clear", []
    for act in SENTINEL_PRECEDENCE:
        winners = [r for r in matched if r["action"] == act]
        if winners:
            action = act
            break
    return {"action": action,
            "rule_ids": [r["id"] for r in winners],
            "note": " ; ".join(r["note"] for r in winners),
            "version": version}
