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
import os
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
