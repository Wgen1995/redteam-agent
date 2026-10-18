# -*- coding: utf-8 -*-
"""工具生命周期自纠层（VulnClaw correction_layer 移植·战士化）。

哲学单源（.research/repos/VulnClaw/vulnclaw/agent/correction_layer.py 只读
参考）：刻意不做规划器——只观察工具生命周期事件（调前/调后/批后），把紧凑
事实、健康、时延与循环暗示存进层内状态，让模型下一轮自纠而不被迫走固定
工作流。信号双出口（VulnClaw _append_correction_note 同款）：
  ① 即时：指令结果 summary 追加 [diagnostic] 注记（当轮对话面）；
  ② 持存：take_hints() 排空喂 loop 既有 corrections 列表（次轮上下文
     「上轮纠正信号」节——ContextBuilder.build API 零变更）；
  ③ 钉住事实：pinned_fact_lines() 喂 build(facts_extra=...)（「相关事实」
     节，参 R3 冷折叠执法）。

战士化差异（对 diff 负责，逐条可查）：
- AgentState（跨会话 Pydantic 状态）→ CorrectionLayer 进程内轻状态；一意图
  一实例（R1 一意图一脑：意图间零继承，血缘仍走账本）；
- 事件源=MCP 工具回调 → 战士 loop 的 guard 执行三元组 (rc, stdout, stderr)；
  rc!=0 即失败（卡层拒/guard 拒=1、环境不可用=2 的既有语义）；
- evidence 面（evidence_view 冗余检测/evidence_id）不移植——战士运行时无
  该工具面；其余提取器（旗标/状态码/表单/SQL/URL/路径/JS 端点/链接/
  解析器-过滤器边界/PHP POP 链/语义暗示）原样移植；
- 边界常量同源：hint 上限 24、pinned 上限 80、progress 上限 160、
  调用窗 400（半量淘汰）、慢阈 15000ms、重复窗 8/6。

永不 raise：提取器只读文本；本层任何异常都不该炸主循环（容错律同
protocol.py——解析/观察是循环的地板，不是门）。
"""
import hashlib
import json
import re

__all__ = ["CorrectionSignal", "ToolHealth", "CorrectionLayer",
           "content_digest", "correction_note"]

_URL_RE = re.compile(r"https?://[^\s'\"<>）)]+", re.IGNORECASE)
_PATH_RE = re.compile(r"(?<![\w-])/[A-Za-z0-9._~!$&'()*+,;=:@%/-]{2,120}")
_ATTR_RE = re.compile(r"""(?i)\b([a-z_:][-a-z0-9_:.]*)\s*=\s*["']?([^"'\s>]+)""")
_FORM_RE = re.compile(r"(?is)<form\b[^>]*>")
_INPUT_RE = re.compile(r"(?is)<input\b[^>]*>")
_LINK_RE = re.compile(
    r"""(?is)\b(?:href|src)\s*=\s*["']([^"']{1,180}(?:\.php\b|\.js\b|/api/?|api/)[^"']*)["']""")
_JS_ENDPOINT_RE = re.compile(
    r"""(?is)(?:url\s*[:=]\s*|fetch\s*\(|axios\.\w+\s*\()\s*["']([^"']{1,180}(?:\.php\b|/api/?|api/|\?)[^"']*)["']""")
_SQL_SNIPPET_RE = re.compile(
    r"""(?is)(?:\$sql\s*=\s*)?["']?\s*(select\s+.{0,260}?\s+from\s+.{0,260}?(?:where|limit)\s+.{0,420}?)(?:["';\n]|$)""")
_PHP_SERIALIZE_FILTER_RE = re.compile(
    r"""(?is)(?:preg_match|regex|filter|REGEX_HIT|filter_hit).{0,260}(?:\[oc\]|[oc]).{0,80}\\d\+""")
_FLAG_RE = re.compile(r"\b[a-z]{1,8}\{[^}\s]{1,120}\}", re.IGNORECASE)
_PARSER_FILTER_HINT_PREFIX = "Parser/filter differential:"
_IGNORED_URL_PARTS = (
    "urllib3.readthedocs.io",
    "pythonhosted.org/urllib3",
    "requests.readthedocs.io",
)
_IGNORED_HTML_PSEUDO_PATHS = {
    "/a",
    "/b",
    "/br",
    "/code",
    "/div",
    "/em",
    "/i",
    "/li",
    "/p",
    "/pre",
    "/script",
    "/span",
    "/strong",
    "/style",
}
_FAILURE_MARKERS = (
    "[!]",
    "failed locally",
    "traceback",
    "exception",
    "timed out",
    "timeout",
    "connection refused",
    "cancellederror",
    "constraint_violation",
    "role_tool_violation",
)
_PROGRESS_MARKERS = (
    "flag",
    "ctf{",
    "status:",
    "set-cookie",
    "location:",
    "<form",
    "<input",
    "href=",
    "select",
    "union",
    "sql",
    "token",
    "admin",
    "endpoint",
    "source",
    "sink",
    "request=",
    "headers=",
    "cookies=",
    "body=",
    "body_length",
    "hash=",
    "same-body",
    "same body",
    "eval",
    "assert",
    "system(",
    "exec(",
    "shell_exec",
    "unserialize",
    "deserialize",
    "$_get",
    "$_post",
    "$_cookie",
    "$_request",
)
_PARSER_RUNTIME_MARKERS = (
    "unserialize",
    "deserialize",
    "json_decode",
    "simplexml_load",
    "xpath",
    "template",
    "eval(",
    "assert(",
    "include(",
    "require(",
)
_FILTER_MARKERS = (
    "preg_match",
    "regex",
    "filter",
    "blacklist",
    "waf",
    "blocked",
    "regex_hit",
    "filter_hit",
)

# 边界常量（VulnClaw agent_state 同源）
SLOW_MS = 15_000
MAX_TOOL_CALLS = 400
MAX_PROGRESS_SIGNALS = 160
MAX_PINNED_FACTS = 80
MAX_CORRECTION_HINTS = 24


def _one_line(value, limit=240):
    """压空白+截断的单行化（VulnClaw one_line 确定性版）。"""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:max(0, int(limit))]


def _extract_flags(text):
    """提取 flag 形 token（不断言有效性——VulnClaw extract_flags 同款）。"""
    return list(dict.fromkeys(_FLAG_RE.findall(text or "")))


def content_digest(text):
    """稳定摘要（测试与追溯分析用——VulnClaw content_digest 同款）。"""
    return hashlib.sha256(str(text or "").encode(
        "utf-8", errors="replace")).hexdigest()[:16]


def correction_note(pre_hint, post_hint):
    """[diagnostic] 注记行（VulnClaw _append_correction_note 的注记面）。"""
    notes = [item for item in (pre_hint, post_hint) if item]
    if not notes:
        return ""
    return "[diagnostic] %s" % " ".join(notes)


class CorrectionSignal(object):
    """单次工具调用的观察结果（VulnClaw CorrectionSignal 移植）。"""

    __slots__ = ("tool", "ok", "duration_ms", "rc", "progress", "hints")

    def __init__(self, tool, ok, duration_ms=0, rc=0):
        self.tool = tool
        self.ok = bool(ok)
        self.duration_ms = max(0, int(duration_ms or 0))
        self.rc = int(rc)
        self.progress = []
        self.hints = []

    def model_hint(self):
        parts = [*self.progress, *self.hints]
        return "; ".join(_one_line(item, 220) for item in parts if item)


class ToolHealth(object):
    """工具健康（VulnClaw ToolHealth 移植：status/failures/successes/…）。"""

    __slots__ = ("tool", "status", "failures", "successes",
                 "consecutive_failures", "last_error", "last_duration_ms")

    def __init__(self, tool):
        self.tool = tool
        self.status = "healthy"
        self.failures = 0
        self.successes = 0
        self.consecutive_failures = 0
        self.last_error = ""
        self.last_duration_ms = 0


class CorrectionLayer(object):
    """一意图一层的自纠观察面（R1：意图间零继承）。

    用法（loop 集成）：
        corr = CorrectionLayer()
        pre = corr.before_tool_call(card, args)          # 软预检，不阻执行
        signal = corr.after_tool_call(card, args, raw,
                                      duration_ms=ms, rc=rc, error=err)
        note = correction_note(pre, signal.model_hint())  # 追加进指令结果
        corr.after_tool_batch(signals)                    # 批后暗示
        corrections.extend(corr.take_hints())             # 次轮「上轮纠正信号」
        facts_extra=corr.pinned_fact_lines()              # 「相关事实」节
    """

    def __init__(self, slow_ms=SLOW_MS):
        self.slow_ms = max(0, int(slow_ms))
        self._calls = []            # [(tool, key_args)] 有界
        self._health = {}           # tool -> ToolHealth
        self._hints = []            # 去重有界
        self._pinned = []           # [(tool, text)] 去重有界
        self._progress = []         # [detail] 有界

    # ---- 观察面（调前/调后/批后）----

    def before_tool_call(self, tool, arguments):
        """调前软暗示（重复/降级）。永不阻断执行——返回 '' 即无话可说。"""
        hints = []
        repeated = self._count_recent(tool, arguments, window=8)
        if repeated >= 2:
            hints.append(
                "Exact tool call %s has already appeared %d times recently; "
                "recent repetition may be low-value unless there is a new "
                "reason." % (tool, repeated))
        health = self._health.get(tool)
        if health is not None and health.status == "degraded":
            hints.append(
                "%s is currently degraded after %d failure(s); account for "
                "this tool-health signal when choosing actions."
                % (tool, health.consecutive_failures))
        return " ".join(hints)

    def after_tool_call(self, tool, arguments, raw_output,
                        duration_ms=0, rc=0, error=None):
        """调后落健康/进展/钉住事实，返回模型可见暗示（CorrectionSignal）。"""
        raw = str(raw_output or "")
        lower = raw.lower()
        ok = (int(rc) == 0 and error is None
              and not any(marker in lower for marker in _FAILURE_MARKERS))
        signal = CorrectionSignal(tool=tool, ok=ok,
                                  duration_ms=duration_ms, rc=rc)
        self._record_call(tool, arguments)

        error_text = _one_line(
            str(error or "").strip() or _first_failure_line(raw)
            or (("rc=%d" % int(rc)) if rc else ""), 220)
        self._record_tool_health(tool=tool, ok=ok,
                                 duration_ms=duration_ms,
                                 error=error_text)

        if int(duration_ms) >= self.slow_ms:
            hint = ("Diagnostic: %s took %dms; recent tool latency is high."
                    % (tool, int(duration_ms)))
            signal.hints.append(hint)
            self._add_hint(hint)

        if not ok:
            hint = ("Diagnostic: %s failed or returned an error; this "
                    "result is tool-health evidence." % tool)
            signal.hints.append(hint)
            self._add_hint(hint)
            return signal

        progress = _extract_progress(raw)
        for detail in progress:
            self._record_progress(detail)
            signal.progress.append(detail)

        for fact in _extract_pinned_facts(raw):
            self._pin_fact(tool, fact)

        for hint in _extract_semantic_hints(raw, self):
            signal.hints.append(hint)
            self._add_hint(hint)

        if (not progress
                and self._count_recent(tool, arguments, window=6) >= 2):
            hint = ("Diagnostic: repeated %s arguments produced no obvious "
                    "new signal." % tool)
            signal.hints.append(hint)
            self._add_hint(hint)
        return signal

    def after_tool_batch(self, signals):
        """批后短暗示（全败/慢工具）——有用才说，返回 '' 即无。"""
        if not signals:
            return ""
        failed = [item for item in signals if not item.ok]
        slow = [item for item in signals
                if item.duration_ms >= self.slow_ms]
        hint = ""
        if len(failed) == len(signals):
            hint = "Diagnostic: all tool calls in this batch failed."
        elif slow:
            names = ", ".join(item.tool for item in slow[:3])
            hint = "Diagnostic: slow tool(s) observed: %s." % names
        if hint:
            self._add_hint(hint)
        return hint

    # ---- 出口面（次轮上下文供给）----

    def take_hints(self):
        """排空持存暗示（去重有界——次轮「上轮纠正信号」节供给）。"""
        out = list(self._hints)
        self._hints = []
        return out

    def pinned_fact_lines(self):
        """钉住事实 → facts_extra 行（<tool> | tool-pin | <text>）。"""
        return ["%s | tool-pin | %s" % (tool, text)
                for tool, text in self._pinned]

    def health(self, tool):
        return self._health.get(tool)

    # ---- 内部状态面（VulnClaw agent_state 同源语义）----

    def _record_call(self, tool, arguments):
        try:
            key_args = json.dumps(list(arguments or []),
                                  ensure_ascii=False)[:500]
        except (TypeError, ValueError):
            key_args = str(arguments or "")[:500]
        self._calls.append((str(tool), key_args))
        if len(self._calls) > MAX_TOOL_CALLS:
            del self._calls[:MAX_TOOL_CALLS // 2]

    def _count_recent(self, tool, arguments, window):
        try:
            key_args = json.dumps(list(arguments or []),
                                  ensure_ascii=False)[:500]
        except (TypeError, ValueError):
            key_args = str(arguments or "")[:500]
        recent = self._calls[-max(1, int(window or 1)):]
        return sum(1 for t, k in recent if t == tool and k == key_args)

    def _record_tool_health(self, tool, ok, duration_ms, error):
        current = self._health.get(tool) or ToolHealth(tool)
        current.last_duration_ms = max(0, int(duration_ms or 0))
        if ok:
            current.status = "healthy"
            current.successes += 1
            current.consecutive_failures = 0
            current.last_error = ""
        else:
            current.status = "degraded"
            current.failures += 1
            current.consecutive_failures += 1
            current.last_error = _one_line(error, 220)
        self._health[tool] = current

    def _record_progress(self, detail):
        line = _one_line(detail, 260)
        if line:
            self._progress.append(line)
            if len(self._progress) > MAX_PROGRESS_SIGNALS:
                del self._progress[:MAX_PROGRESS_SIGNALS // 2]

    def _pin_fact(self, tool, text):
        fact_text = _one_line(text, 260)
        if not fact_text:
            return
        normalized = fact_text.lower()
        if any(t.lower() == normalized for _, t in self._pinned):
            return
        self._pinned.append((str(tool), fact_text))
        if len(self._pinned) > MAX_PINNED_FACTS:
            del self._pinned[:MAX_PINNED_FACTS // 2]

    def _add_hint(self, hint):
        text = _one_line(hint, 320)
        if not text:
            return
        if any(item.lower() == text.lower() for item in self._hints):
            return
        self._hints.append(text)
        self._hints = self._hints[-MAX_CORRECTION_HINTS:]


# ---- 提取器（VulnClaw correction_layer 私有面原样移植）----

def _first_failure_line(raw):
    for line in str(raw or "").splitlines():
        stripped = line.strip()
        if stripped and any(marker in stripped.lower()
                            for marker in _FAILURE_MARKERS):
            return _one_line(stripped, 220)
    return ""


def _extract_progress(raw):
    text = str(raw or "")
    lower = text.lower()
    progress = []

    for flag in _extract_flags(text)[:3]:
        progress.append("flag-like token observed: %s" % flag)

    status = re.search(r"(?:Status|HTTP/\d(?:\.\d)?)\s*:?\s*(\d{3})",
                       text, re.IGNORECASE)
    if status:
        progress.append("HTTP status observed: %s" % status.group(1))

    if any(marker in lower for marker in ("<form", "<input", "name=")):
        progress.append("HTML form/input surface observed")

    if _extract_sql_facts(text):
        progress.append("server-side SQL/source snippet observed")

    if _extract_js_endpoint_facts(text):
        progress.append("JS/API endpoint construction observed")

    if _extract_parser_filter_facts(text):
        progress.append("parser/filter boundary observed")

    if _extract_php_pop_chain_facts(text):
        progress.append("PHP POP/deserialization chain observed")

    urls = _filtered_urls(text)[:5]
    if urls:
        progress.append("URL(s) observed: "
                        + ", ".join(_one_line(url, 80) for url in urls[:3]))

    endpoints = [item for item in dict.fromkeys(_PATH_RE.findall(text))
                 if _is_meaningful_path(item)][:5]
    if endpoints:
        progress.append("path(s) observed: " + ", ".join(endpoints[:4]))

    if not progress and any(marker in lower
                            for marker in _PROGRESS_MARKERS):
        progress.append("security-relevant marker observed in tool output")

    return progress[:6]


def _is_meaningful_path(path):
    value = str(path or "").strip()
    lower = value.lower().rstrip(">:\"'")
    if not lower or lower.startswith(("//", "/usr/", "/lib/",
                                      "/site-packages/")):
        return False
    if lower in _IGNORED_HTML_PSEUDO_PATHS:
        return False
    if lower.startswith(("/span", "/code", "/br", "/i'", "/font")):
        return False
    return True


def _extract_pinned_facts(raw):
    text = str(raw or "")
    facts = []
    for flag in _extract_flags(text)[:3]:
        facts.append("Observed flag-like token: %s" % flag)
    facts.extend(_extract_sql_facts(text))
    facts.extend(_extract_form_facts(text))
    facts.extend(_extract_js_endpoint_facts(text))
    facts.extend(_extract_link_facts(text))
    facts.extend(_extract_parser_filter_facts(text))
    facts.extend(_extract_php_pop_chain_facts(text))
    for url in _filtered_urls(text)[:5]:
        facts.append("Observed URL: %s" % _one_line(url, 160))
    return list(dict.fromkeys(facts))[:14]


def _filtered_urls(text):
    """目标/用户 URL 保留，依赖告警文档链忽略（VulnClaw 同款过滤）。"""
    urls = []
    for url in dict.fromkeys(_URL_RE.findall(text or "")):
        lowered = url.lower()
        if any(part in lowered for part in _IGNORED_URL_PARTS):
            continue
        urls.append(url)
    return urls


def _extract_attrs(tag):
    attrs = {}
    for key, value in _ATTR_RE.findall(tag or ""):
        attrs[key.lower()] = value
    return attrs


def _extract_sql_facts(text):
    facts = []
    for line in str(text or "").splitlines():
        lower = line.lower()
        if "select" not in lower or " from " not in lower:
            continue
        if not any(marker in lower for marker in (" where ", "$_get",
                                                  " limit ", " union ")):
            continue
        snippet = _one_line(line, 300)
        if snippet:
            facts.append("Source SQL: %s" % snippet)
        if len(facts) >= 4:
            return list(dict.fromkeys(facts))
    if facts:
        return list(dict.fromkeys(facts))
    for match in _SQL_SNIPPET_RE.finditer(text or ""):
        snippet = _one_line(match.group(1), 300)
        if snippet:
            facts.append("Source SQL: %s" % snippet)
        if len(facts) >= 4:
            break
    return list(dict.fromkeys(facts))


def _extract_form_facts(text):
    facts = []
    for tag in _FORM_RE.findall(text or "")[:4]:
        attrs = _extract_attrs(tag)
        parts = []
        if attrs.get("method"):
            parts.append("method=%s" % attrs["method"])
        if attrs.get("action"):
            parts.append("action=%s" % attrs["action"])
        if parts:
            facts.append("HTML form: " + " ".join(parts))
    for tag in _INPUT_RE.findall(text or "")[:8]:
        attrs = _extract_attrs(tag)
        name = attrs.get("name") or attrs.get("id")
        if not name:
            continue
        detail = ("name=%s" % name if attrs.get("name")
                  else "id=%s" % name)
        if attrs.get("type"):
            detail += " type=%s" % attrs["type"]
        facts.append("HTML input: %s" % detail)
    return facts[:8]


def _extract_js_endpoint_facts(text):
    facts = []
    for match in _JS_ENDPOINT_RE.finditer(text or ""):
        endpoint = _one_line(match.group(1), 180)
        if endpoint:
            facts.append("JS/API endpoint: %s" % endpoint)
        if len(facts) >= 6:
            break
    return facts


def _extract_link_facts(text):
    facts = []
    for match in _LINK_RE.finditer(text or ""):
        endpoint = _one_line(match.group(1), 180)
        if endpoint:
            facts.append("Linked endpoint: %s" % endpoint)
        if len(facts) >= 8:
            break
    return facts


def _extract_parser_filter_facts(text):
    """钉住解析器/过滤器边界，不处方式一动作（VulnClaw 同款）。"""
    raw = str(text or "")
    lower = raw.lower()
    if not raw.strip():
        return []
    has_runtime_parser = any(marker in lower
                             for marker in _PARSER_RUNTIME_MARKERS)
    has_filter = any(marker in lower for marker in _FILTER_MARKERS)
    has_numeric_grammar_regex = bool(re.search(r"\\d\+|\[\w*\]|[+*?]",
                                               raw))
    has_php_serialized_shape = bool(
        re.search(r"(?<![A-Za-z0-9_])[OC]:\d+:", raw))
    if _PHP_SERIALIZE_FILTER_RE.search(raw) or (
            has_runtime_parser and has_filter and has_php_serialized_shape):
        return [
            "Parser/filter boundary: PHP serialized input is checked by a "
            "regex/string filter before unserialize; parser/filter behavior "
            "may differ across lexical variants and runtime versions."
        ]
    if has_runtime_parser and has_filter and has_numeric_grammar_regex:
        return [
            "Parser/filter boundary: input is filtered by regex/string "
            "logic before a runtime parser/interpreter; filter behavior "
            "and parser behavior may not be equivalent."
        ]
    return []


def _extract_php_pop_chain_facts(text):
    """源码证据里的通用 PHP POP 链构造暗示（VulnClaw 同款）。"""
    raw = str(text or "")
    lower = raw.lower()
    if not ("unserialize" in lower and "__destruct" in lower
            and any(marker in lower
                    for marker in ("eval(", "assert(", "system(",
                                   "exec("))):
        return []
    entry = ""
    sink = ""
    entry_match = re.search(
        r"(?is)class\s+([A-Za-z_][A-Za-z0-9_]*)\b"
        r"(?:(?!class\s+[A-Za-z_]).)*?function\s+__destruct\s*\(",
        raw)
    if entry_match:
        entry = entry_match.group(1)
    sink_match = re.search(
        r"(?is)class\s+([A-Za-z_][A-Za-z0-9_]*)\b"
        r"(?:(?!class\s+[A-Za-z_]).)*?"
        r"(?:eval|assert|system|exec)\s*\(",
        raw)
    if sink_match:
        sink = sink_match.group(1)
    names = []
    if entry:
        names.append("entry=%s" % entry)
    if sink and sink != entry:
        names.append("sink=%s" % sink)
    suffix = (" (%s)" % ", ".join(names)) if names else ""
    return [
        "PHP POP chain candidate: unserialize reaches a magic method and "
        "dangerous sink%s; object graph entry/sink relationship is "
        "relevant to exploitability." % suffix
    ]


def _extract_semantic_hints(raw, layer):
    """小体量证据背书诊断——不替模型规划（VulnClaw 同款，state 面适配）。"""
    text = str(raw or "")
    lower = text.lower()
    hints = []
    sql_facts = _extract_sql_facts(text)
    pinned_texts = [t for _, t in getattr(layer, "_pinned", [])]
    pinned_sql = [item for item in pinned_texts
                  if "source sql:" in item.lower()]
    has_sql_source = bool(sql_facts or pinned_sql)
    if sql_facts:
        hints.append(
            "Diagnostic: SQL source is visible; the exact server-side "
            "expression, quoting and trailing syntax are high-value "
            "context for any SQLi hypothesis.")
    parser_filter_facts = _extract_parser_filter_facts(text)
    pinned_parser_filter = [item for item in pinned_texts
                            if "parser/filter boundary:" in item.lower()]
    if parser_filter_facts or pinned_parser_filter:
        hints.append(
            "%s regex/string filter guards a runtime parser. Parser/filter "
            "mismatch is an open hypothesis; local or remote differential "
            "experiments are optional tools if they fit the model's "
            "strategy." % _PARSER_FILTER_HINT_PREFIX)
    php_pop_facts = _extract_php_pop_chain_facts(text)
    pinned_php_pop = [item for item in pinned_texts
                      if "php pop chain candidate:" in item.lower()]
    if php_pop_facts or pinned_php_pop:
        hints.append(
            "Diagnostic: PHP deserialization POP evidence includes a "
            "magic-method entry and a dangerous sink; entry/sink property "
            "relationships remain relevant context.")
    if ("remote_verification_required" in lower
            or ("target_runtime=php/5" in lower
                and "local_runtime=php/" in lower
                and "signed object/class length" in lower)):
        hints.append(
            "Diagnostic: runtime compatibility evidence suggests local "
            "parser results may not fully represent the target runtime.")
    has_request_surface = any(marker in lower for marker in
                              ("request=", "headers=", "cookies=",
                               "body=", "json=", "params="))
    if ("same-body groups" in lower or "same-body" in lower) \
            and has_request_surface:
        hints.append(
            "Diagnostic: same-body probe results were observed with an "
            "audited request surface; response equivalence and request "
            "delivery remain part of the evidence context.")
    used_comment_terminator = any(marker in lower
                                  for marker in ("%23", "%2d%2d", "--+", "#"))
    no_flag = not _extract_flags(text)
    if has_sql_source and used_comment_terminator and no_flag:
        hints.append(
            "Diagnostic: pinned SQL source plus failed comment-terminated "
            "probes leaves SQL closure/operator assumptions unresolved.")
    return list(dict.fromkeys(hints))[:3]
