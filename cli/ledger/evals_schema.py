# -*- coding: utf-8 -*-
"""契约 15 指标集 schema 加载+校验单源（批次 6；标准库零依赖）。

必填字段/枚举/重复 id 校验（契约 15 §1）；runner 未注册不在 schema 层绑运行时——
run_suite 阶段才判 ENV-SKIP（契约 15 §1 违例行口径）。"""
import json

_ENUMS = {"layer": {"L1", "L2", "L3"}, "gate": {"hard", "warn"},
          "kind": {"equality", "threshold", "zero-tolerance", "checklist"}}
_REQUIRED = ["id", "layer", "gate", "kind", "title", "baseline", "source", "desc"]
_ID_PREFIX = ("M", "X")  # X*=测试合成指标；正式面 M\\d\\d-*


class MetricsError(Exception):
    pass


def validate_metric(m):
    errs = []
    for k in _REQUIRED:
        if k not in m:
            errs.append("缺字段 %s" % k)
    for k, allowed in _ENUMS.items():
        if k in m and m[k] not in allowed:
            errs.append("%s 枚举外: %r" % (k, m[k]))
    b = m.get("baseline") or {}
    if "value" not in b:
        errs.append("baseline.value 缺")
    s = m.get("source") or {}
    if "runner" not in s or "args" not in s:
        errs.append("source.runner/args 缺")
    return errs


def load_metrics(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("format_version") != 1:
        raise MetricsError("format_version != 1")
    seen = set()
    for m in data.get("metrics", []):
        errs = validate_metric(m)
        if errs:
            raise MetricsError("%s: %s" % (m.get("id", "?"), "; ".join(errs)))
        if m["id"] in seen:
            raise MetricsError("指标 id 重复: %s" % m["id"])
        seen.add(m["id"])
    return data
