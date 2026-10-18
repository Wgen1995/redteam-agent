# -*- coding: utf-8 -*-
"""差分探测器(功能6·设计§2 核心件)——同一请求模板×身份集×状态集全组合,响应差分四轴。

输入: 请求模板(方法/URL/头/体,可含 {identity}/{state} 槽)×身份集(身份矩阵钥匙,
凭据以 {{vault:cred-N}} 占位符注入——真值永不进本层)×状态集(状态前/状态后/取消后…)。
输出: 响应差分表(状态码/body哈希/长度/关键头 四轴)。

纪律:
- 诚实律(RT-0006): 零差分=无信号,verdict=no-signal 如实入报,不脑补候选;
  信标型响应(marker 全等)同样零信息——不因「该有洞」而立卡。
- 噪声门: norm 哈希(ledger/norm 单源,nonce/ts 已归一)相等而仅长度差=动态字段
  残差 → class=noise 不计信号——防 nonce 噪声污染候选池。
- 预算警戒(RT-0006 matrix 128 行只 15x): 组合数>pair_cap → DiffBudgetError
  拒收(缺省 24=write_cmds.AUTHZ_DIFF_PAIR_CAP 同值,可 pair_cap 覆盖);
  显式 override_budget=True 放行但报告留 budget_overridden 痕。
- 方法族(RT-0006): 模板 method 缺省 GET 直取——POST 是显式决定不是缺省。
- 挂链(RT-0016): 每格携带身份 auth_context=CRED-{id},下游 finding 直取挂链。
- 执行后端: 本模块零 HTTP 栈;sender 注入,生产装配=CurlSender(tools.gate curl 卡,
  经 guard 门链: scope/限速/vault 执行点回注全数生效)。
- 稳定律(差分四原则3): repeats≥2 时两次指纹不同=unstable,confidence 降级注记。
"""
import hashlib

from ledger.norm import normalize_artifact

AXES = ("status", "body_hash", "length", "headers")
DEFAULT_KEY_HEADERS = ("content-type", "location", "www-authenticate",
                       "x-auth-token", "x-request-id", "retry-after")
DEFAULT_METHOD = "GET"


class DiffBudgetError(Exception):
    """组合数超 pair_cap(RT-0006 矩阵预算警戒)——拒收,裁剪或显式覆盖。"""


class SenderError(Exception):
    """执行后端失败(rc!=0/异常)——格如实记 error,不吞不猜。"""

    def __init__(self, rc, err):
        Exception.__init__(self, "sender rc=%s err=%s" % (rc, (err or "").strip()))
        self.rc = rc
        self.err = err


class Response(object):
    """响应指纹源: status/headers(小写键)/body(文本)。"""

    __slots__ = ("status", "headers", "body")

    def __init__(self, status, headers, body):
        self.status = int(status)
        self.headers = dict(headers or {})
        self.body = body or ""


def fingerprint(response, key_headers=DEFAULT_KEY_HEADERS,
               normalizer=normalize_artifact):
    """四轴指纹: 状态码/body哈希(norm 单源)/长度/关键头投影。"""
    body = response.body or ""
    norm = normalizer(body) if normalizer else body
    return {"status": int(response.status),
            "body_hash": hashlib.sha256(norm.encode("utf-8", "replace")).hexdigest(),
            "length": len(body.encode("utf-8", "replace")),
            "headers": {k: (response.headers or {}).get(k, "") for k in key_headers}}


def _sub(text, mapping):
    out = str(text or "")
    for k, v in mapping.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def render(template, identity, state):
    """模板×身份×状态 → 具体请求。身份槽={{vault:cred-N}} 占位符(vault 纪律);
    匿名(secret_ref 空)渲染出的空头整头删除——空凭据头=携带形态噪音。"""
    state = {"name": state} if isinstance(state, str) else (state or {})
    mapping = {"identity": identity.get("secret_ref", ""),
               "state": state.get("name", "")}
    mapping.update(identity.get("vars", {}) or {})
    mapping.update(state.get("vars", {}) or {})
    headers = {}
    for k, v in (template.get("headers") or {}).items():
        rv = _sub(v, mapping)
        if rv:
            headers[k] = rv
    return {"method": (template.get("method") or DEFAULT_METHOD).upper(),
            "url": _sub(template.get("url", ""), mapping),
            "headers": headers,
            "body": _sub(template.get("body", ""), mapping),
            "identity": identity.get("label", ""),
            "state": state.get("name", ""),
            "auth_context": identity.get("auth_context", "")}


def curl_argv(request, max_time=10):
    """请求→curl 卡参数(不含 binary;URL 居末=CLI 卡目标位惯例)。纯函数不执行。"""
    argv = ["-sS", "--max-time", str(max_time),
            "-X", request.get("method") or DEFAULT_METHOD]
    for k, v in (request.get("headers") or {}).items():
        argv += ["-H", "%s: %s" % (k, v)]
    if request.get("body"):
        argv += ["--data-raw", request["body"]]
    argv += ["-D", "-", request.get("url", "")]
    return argv


def parse_curl_out(out):
    """curl -D - 输出 → (status, headers 小写键, body)。头块/体块以首个空行切分。"""
    text = out or ""
    head, body = text, ""
    for sep in ("\r\n\r\n", "\n\r\n", "\n\n", "\r\n\n"):
        if sep in text:
            head, body = text.split(sep, 1)
            break
    else:
        if "\n" in text:
            head, body = text.split("\n", 1)
    status, headers = 0, {}
    for ln in head.split("\n"):
        ln = ln.replace("\r", "")
        if not ln.strip():
            continue
        parts = ln.split(" ", 2)
        if parts[0].upper().startswith("HTTP/") and len(parts) > 1 and parts[1].isdigit():
            status = int(parts[1])
            continue
        if ":" in ln:
            k, _, v = ln.partition(":")
            headers[k.strip().lower()] = v.strip()
    return status, headers, body


class CurlSender(object):
    """既有执行后端装配: tools.gate.execute(goal_dir,"curl",args,ts)——卡层门链+
    guard(scope/限速/vault 执行点回注)全数生效;本类只做 argv 组装与输出解析。
    exec_fn 注入位=单测假件直挂(生产缺省走 gate)。"""

    def __init__(self, goal_dir, exec_fn=None, ts="", max_time=10):
        self.goal_dir = goal_dir
        self.exec_fn = exec_fn
        self.ts = ts
        self.max_time = max_time

    def _backend(self):
        if self.exec_fn is not None:
            return self.exec_fn
        from tools import gate   # 惰性: 生产装配才触 CLI 面
        return gate.execute

    def __call__(self, request):
        argv = curl_argv(request, max_time=self.max_time)
        rc, out, err = self._backend()(self.goal_dir, "curl", argv[1:], self.ts)
        if rc != 0:
            raise SenderError(rc, err)
        status, headers, body = parse_curl_out(out)
        return Response(status, headers, body)


def _default_cap():
    try:
        from ledger.write_cmds import AUTHZ_DIFF_PAIR_CAP   # 单源同值
        return AUTHZ_DIFF_PAIR_CAP
    except Exception:   # noqa: BLE001 —— write_cmds 不可导入时退回同值缺省
        return 24


def _diff_one(axis, base_fp, fp):
    """单轴差分记录;无差返回 None。"""
    if axis == "headers":
        keys = [k for k in base_fp["headers"] if base_fp["headers"][k] != fp["headers"][k]]
        if not keys:
            return None
        return {"axis": "headers", "baseline": {k: base_fp["headers"][k] for k in keys},
                "value": {k: fp["headers"][k] for k in keys}}
    if base_fp[axis] == fp[axis]:
        return None
    return {"axis": axis, "baseline": base_fp[axis], "value": fp[axis]}


def _classify(axis, base_fp, fp):
    """噪声门: 仅长度差(norm 哈希同/状态同/头同)=动态字段残差→noise,余→signal。"""
    only_len = (axis == "length" and base_fp["status"] == fp["status"]
                and base_fp["body_hash"] == fp["body_hash"]
                and base_fp["headers"] == fp["headers"])
    return "noise" if only_len else "signal"


def probe(template, identities, states, sender, repeats=1, pair_cap=None,
          override_budget=False, key_headers=DEFAULT_KEY_HEADERS,
          normalizer=normalize_artifact):
    """差分探测主入口: 模板×身份×状态全组合发送→四轴差分表+诚实裁决。

    identities: [{label,secret_ref,auth_context,vars?}](identity_matrix 产物或最小形);
    states: [name 或 {name,vars}];对照=anonymous(在场时),缺省首身份;
    身份轴差分=同状态内 vs 对照身份;状态轴差分=同身份 vs 首状态。
    返回报告 dict(verdict∈{signal,no-signal,errors})。
    """
    cap = _default_cap() if pair_cap is None else int(pair_cap)
    combos = len(identities) * len(states)
    if combos > cap and not override_budget:
        raise DiffBudgetError(
            "差分组合数 %d 超 pair_cap=%d(RT-0006 矩阵预算警戒: "
            "裁剪身份/状态集,或 override_budget=True 显式放行)" % (combos, cap))
    states = [s if isinstance(s, dict) else {"name": s} for s in states]
    base_label = next((i["label"] for i in identities
                       if i.get("label") == "anonymous"), identities[0]["label"])
    cells, notes = [], []
    fps = {}   # (label, state_name) -> fingerprint
    for st in states:
        for ident in identities:
            req = render(template, ident, st)
            fps_list, err = [], ""
            for _ in range(max(1, int(repeats))):
                try:
                    fps_list.append(fingerprint(sender(req), key_headers, normalizer))
                except SenderError as e:
                    err = str(e)
                    break
                except Exception as e:   # noqa: BLE001 —— 通道异常如实记格
                    err = "sender-exception: %s" % e
                    break
            unstable = len(fps_list) >= 2 and any(f != fps_list[0] for f in fps_list[1:])
            fp = fps_list[0] if fps_list else None
            cells.append({"identity": req["identity"], "state": req["state"],
                          "auth_context": req["auth_context"], "request": req,
                          "fingerprint": fp, "error": err, "unstable": unstable})
            if fp is not None:
                fps[(req["identity"], req["state"])] = fp
            if unstable:
                notes.append("unstable: %s×%s 两次指纹不同(confidence 降一级,四原则3)"
                             % (req["identity"], req["state"]))
    first_state = states[0]["name"]
    diffs, signals = [], []
    for st in states:
        for ident in identities:
            label = ident["label"]
            fp = fps.get((label, st["name"]))
            if fp is None:
                continue
            comparisons = []
            if label != base_label:
                comparisons.append(("identity", (base_label, st["name"])))
            if st["name"] != first_state:
                comparisons.append(("state", (label, first_state)))
            for scope, base_key in comparisons:
                bfp = fps.get(base_key)
                if bfp is None:
                    continue
                for axis in AXES:
                    d = _diff_one(axis, bfp, fp)
                    if d is None:
                        continue
                    d.update({"identity": label, "state": st["name"],
                             "scope": scope, "class": _classify(axis, bfp, fp)})
                    diffs.append(d)
                    if d["class"] == "signal":
                        signals.append(d)
    n_err = sum(1 for c in cells if c["error"])
    if n_err:
        notes.append("error_cells=%d(执行通道失败格如实记,不入差分)" % n_err)
    if not fps:
        verdict = "errors"
        notes.append("全部组合执行失败: 差分不可判(不猜)")
    elif signals:
        verdict = "signal"
    else:
        verdict = "no-signal"
        notes.append("零差分=无信号(RT-0006): 不立候选不脑补;信标型响应零信息同律")
    report = {"template": template, "combo_count": combos, "pair_cap": cap,
              "budget_overridden": bool(combos > cap and override_budget),
              "baseline": base_label, "cells": cells, "diffs": diffs,
              "signals": signals, "verdict": verdict, "notes": notes}
    if report["budget_overridden"]:
        notes.append("budget_overridden: 组合 %d>cap %d 显式放行(留痕)" % (combos, cap))
    return report
