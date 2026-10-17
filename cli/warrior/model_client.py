# -*- coding: utf-8 -*-
"""模型客户端（W5 战士 MVP）——llmpool 判定核的第一个真实消费者。

接线面（本模块=「判定核×HTTP 真调用」之间的薄层）：
- 通道选择：pool.pick(chain)——健康链序首个（chain=[{"name":…}]，池键=name
  唯一道号，避免同 model 名多道混淆）；
- 错误分类：HTTPError/URLError/超时→llmpool.classify（400/取消=no_failover
  保守不切道；401/402/403/404=hard 一次熔断；429=rate 软道 1min 冷却；
  408/5xx/网络=server 软道长档）；
- 冷却/切道：软计数连续 3 次熔断进冷却窗，pick 自动跳过冷却道——调用方
  无感知地换道重试（attempts 全程留痕）。

HTTP 面：stdlib urllib 直连 openai 兼容 /chat/completions
（judge_client 同款：ProxyHandler({}) 绕环境代理、temperature=0、fail-closed
不外抛）。usage 缺失时以 estimate_tokens 估算入账（预算计量 fail-open）。

测试铁律：一切模型面测试指向本地假模型服务（动态口 fixture），绝不真调
外部 API。
"""
import json
import socket
import urllib.error
import urllib.request

from .context import estimate_tokens

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
TEMPERATURE = 0
MAX_TOKENS = 4096
_MAX_ATTEMPTS_PER_CHANNEL = 3      # 软道熔断阈值对齐（3 次软失败即切）


class Reply(object):
    """chat() 结果：ok/content/model/prompt_tokens/completion_tokens/
    reason/attempts[{model, outcome}]。fail-closed：ok=False 不外抛。"""

    __slots__ = ("ok", "content", "model", "prompt_tokens",
                 "completion_tokens", "reason", "attempts")

    def __init__(self, ok, content="", model="", prompt_tokens=0,
                 completion_tokens=0, reason="", attempts=None):
        self.ok = ok
        self.content = content
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.reason = reason
        self.attempts = list(attempts or [])


class ModelClient(object):
    """多道模型客户端：chat(messages) → Reply（llmpool 选道+故障转移）。"""

    def __init__(self, channels, pool, timeout=10.0):
        if not channels:
            raise ValueError("channels 不可为空")
        self.channels = list(channels)
        self.pool = pool
        self.timeout = timeout
        self._chain = [{"name": c["name"]} for c in self.channels]
        self._by_name = {c["name"]: c for c in self.channels}

    # ---- 单道真调用 ----

    def _post(self, channel, messages):
        payload = json.dumps({
            "model": channel.get("model", channel["name"]),
            "messages": messages,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
        }).encode("utf-8")
        base = (channel.get("base_url") or "").rstrip("/")
        url = base if base.endswith("/chat/completions") \
            else base + "/chat/completions"
        req = urllib.request.Request(
            url, data=payload, method="POST",
            headers={"Content-Type": "application/json",
                     "Accept": "application/json",
                     "Authorization": "Bearer " + channel.get("api_key", "")})
        resp = _OPENER.open(req, timeout=self.timeout)
        try:
            return resp.read()
        finally:
            resp.close()

    @staticmethod
    def _parse_envelope(body):
        """openai chat 信封 → (content, finish_reason)；结构不符 ValueError。"""
        doc = json.loads(body.decode("utf-8"))
        if not isinstance(doc, dict):
            raise ValueError("envelope not object")
        choices = doc.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("no choices")
        choice = choices[0]
        if not isinstance(choice, dict):
            raise ValueError("choice not object")
        content = (choice.get("message") or {}).get("content")
        if not isinstance(content, str):
            raise ValueError("content not str")
        return content, choice.get("finish_reason", ""), doc.get("usage")

    # ---- 主入口 ----

    def chat(self, messages):
        attempts = []
        budget = len(self.channels) * _MAX_ATTEMPTS_PER_CHANNEL + 2
        last_reason = ""
        for _ in range(budget):
            entry = self.pool.pick(self._chain)
            if entry is None:
                return Reply(False, reason="all-channels-down",
                             attempts=attempts)
            name = entry["name"]
            channel = self._by_name[name]
            try:
                body = self._post(channel, messages)
            except urllib.error.HTTPError as e:
                code = getattr(e, "code", 0)
                self.pool.report(name, code)
                bucket, _, why = _classify(code)
                attempts.append({"model": name, "outcome": why})
                last_reason = "http-error:%s" % code
                if bucket in ("no_failover",):
                    return Reply(False, reason=last_reason,
                                 attempts=attempts)
                continue
            except (urllib.error.URLError, socket.timeout, TimeoutError,
                    OSError) as e:
                self.pool.report(name, e)
                bucket, _, why = _classify(e)
                attempts.append({"model": name, "outcome": why})
                last_reason = "network-error"
                if bucket == "no_failover":
                    return Reply(False, reason=last_reason,
                                 attempts=attempts)
                continue
            # 2xx：报 ok（清计数/治愈熔断）→ 解析
            self.pool.report(name, 200)
            attempts.append({"model": name, "outcome": "ok"})
            try:
                content, finish, usage = self._parse_envelope(body)
            except (ValueError, UnicodeDecodeError):
                return Reply(False, reason="bad-response",
                             attempts=attempts)
            if finish == "length":
                return Reply(False, model=name, content=content,
                             reason="truncated", attempts=attempts)
            pt, ct = self._usage(usage, messages, content)
            return Reply(True, content=content, model=name,
                         prompt_tokens=pt, completion_tokens=ct,
                         attempts=attempts)
        return Reply(False, reason=last_reason or "exhausted-retries",
                     attempts=attempts)

    @staticmethod
    def _usage(usage, messages, content):
        pt = ct = 0
        if isinstance(usage, dict):
            try:
                pt = int(usage.get("prompt_tokens") or 0)
                ct = int(usage.get("completion_tokens") or 0)
            except (TypeError, ValueError):
                pt = ct = 0
        if pt <= 0:
            pt = sum(estimate_tokens(m.get("content", ""))
                     for m in messages if isinstance(m, dict))
        if ct <= 0:
            ct = estimate_tokens(content)
        return pt, ct


def _classify(err):
    from ledger.llmpool import classify
    return classify(err)
