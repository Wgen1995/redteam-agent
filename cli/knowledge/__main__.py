# -*- coding: utf-8 -*-
"""cli.knowledge 入口（W5 知识环·蒸馏管线 v1）——python3 -m cli.knowledge。

用法：
  python3 -m cli.knowledge distill <battle-dir> [--out DIR]
      [--knowledge-dir DIR] [--min-pattern N] [--min-miss N] [--today DATE]
  python3 -m cli.knowledge confirm <draft.md> --knowledge-dir DIR --reviewer NAME
  python3 -m cli.knowledge report <suite-dir> [--out FILE]

distill：读 battle 结算数据（settle-report+会话三表），规则蒸馏 v1（不调真
模型）→ 技法卡草案（cp 六列）+避坑卡草案（ng 扩列含 ledger_ref）+人工确认
位。**不自动入 cp-index/ng-index——棘轮门管入册。**
confirm：人工确认（review_status: accept）后经 scripts/capability_gate.py
write_negative_card(knowledge_dir, fields, body) 一函落卡（飞轮接口锚）。
report：套件级蒸馏总报（逐战 distill-report.json 聚合）。

退出码：0=成 1=拒（草案未确认/校验不过）2=用法/环境。
"""
import json
import os
import sys

if __package__ in (None, ""):                       # 直跑兼容
    sys.path.insert(0, os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))

from cli.knowledge import distill as D              # noqa: E402

try:
    from ledger.core import ensure_utf8_stdio
    ensure_utf8_stdio()  # Windows 控制台默认 GBK：中文输出统一 UTF-8
except Exception:                                    # ledger 缺席不拦蒸馏本体
    pass

USAGE = ("用法: python3 -m cli.knowledge <子命令> [参数...]\n"
         "  distill <battle-dir> [--out DIR] [--knowledge-dir DIR] "
         "[--min-pattern N] [--min-miss N] [--today DATE]\n"
         "  confirm <draft.md> --knowledge-dir DIR --reviewer NAME\n"
         "  report <suite-dir> [--out FILE]")

_KNOWN = {"--out": "out", "--knowledge-dir": "knowledge_dir",
          "--min-pattern": "min_pattern", "--min-miss": "min_miss",
          "--today": "today", "--reviewer": "reviewer"}


def _parse(rest):
    opts, pos = {}, []
    i = 0
    while i < len(rest):
        tok = rest[i]
        hit = None
        for k, v in _KNOWN.items():
            if tok == k:
                if i + 1 >= len(rest):
                    raise D.DistillError("%s 需要一个值" % k)
                opts[v] = rest[i + 1]
                i += 2
                hit = v
                break
            if tok.startswith(k + "="):
                opts[v] = tok.split("=", 1)[1]
                i += 1
                hit = v
                break
        if hit is None:
            pos.append(tok)
            i += 1
    return opts, pos


def _int_opt(opts, key, default):
    try:
        return int(opts.get(key, default))
    except (TypeError, ValueError):
        raise D.DistillError("--%s 须为整数" % key.replace("_", "-"))


def _default_kd():
    home = os.environ.get("TANYIN_HOME") or os.path.join(
        os.path.expanduser("~"), ".tanyin")
    return os.path.join(home, "knowledge")


def cmd_distill(rest):
    opts, pos = _parse(rest)
    if len(pos) != 1:
        raise D.DistillError("distill 需要恰好一个 <battle-dir>\n" + USAGE)
    rep = D.distill_battle(pos[0], out=opts.get("out"),
                           knowledge_dir=opts.get("knowledge_dir", _default_kd()),
                           min_pattern=_int_opt(opts, "min_pattern", 2),
                           min_miss=_int_opt(opts, "min_miss", 2),
                           today=opts.get("today"))
    c = rep["counts"]
    print("蒸馏完成 %s（代=%s，%s）" % (
        rep["battle"], rep["gen"],
        "已结算 recall=%s" % rep["recall"] if rep["settled"] else "未结算——"
        "漏报族规则不启用（无 GT 面），其余规则照跑"))
    print("  技法卡草案 %d 张（高置信模式）→ 同出目录 techniques/ 子目录"
          % c["technique_drafts"])
    print("  避坑卡草案 %d 张（误报 %d/漏报族 %d/负面披露 %d）→ 同出目录 pitfalls/ 子目录"
          % (c["pitfall_drafts"], c["pitfall_fp"], c["pitfall_miss"], c["pitfall_fact"]))
    for s in rep["skipped"]:
        print("  跳过：%s" % s.get("reason", s))
    print("  未自动入册——每张卡带「人工确认位」（review_status: pending），"
          "人工判读后 confirm 入册（评测棘轮门管）")
    print("  报告 → distill-report.json（同出目录）")
    return 0


def cmd_confirm(rest):
    opts, pos = _parse(rest)
    if len(pos) != 1:
        raise D.DistillError("confirm 需要恰好一个 <draft.md>\n" + USAGE)
    kd = opts.get("knowledge_dir")
    if not kd:
        raise D.DistillError("confirm 需要 --knowledge-dir <运行时库>\n" + USAGE)
    path = D.confirm_draft(pos[0], kd, opts.get("reviewer", ""))
    print("入册完成：%s" % path)
    print("  卡+索引行已经 write_negative_card 原子落盘；knowledge/negative 变更"
          "由评测棘轮（capability_gate）管住——合并前过 GT-scorecard。")
    return 0


def cmd_report(rest):
    opts, pos = _parse(rest)
    if len(pos) != 1:
        raise D.DistillError("report 需要恰好一个 <suite-dir>\n" + USAGE)
    doc = D.suite_report(pos[0])
    out = opts.get("out") or os.path.join(pos[0], "distill-suite-report.json")
    D.gate._atomic_write(out, json.dumps(          # noqa: SLF001  原子写窄面
        doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    c = doc["counts"]
    print("套件蒸馏总报：%d 战在案（%d 已蒸馏，%d 跳过）" % (
        c["battles_seen"], c["battles_distilled"], len(doc["skipped"])))
    print("  技法卡草案合计 %d 张；避坑卡草案合计 %d 张（误报 %d/漏报族 %d/负面披露 %d）"
          % (c["technique_drafts"], c["pitfall_drafts"], c["pitfall_fp"],
             c["pitfall_miss"], c["pitfall_fact"]))
    for s in doc["skipped"]:
        print("  跳过 %s：%s" % (s.get("battle", "?"), s.get("reason", "")))
    print("  报告 → %s" % out)
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        sys.stderr.write(USAGE + "\n")
        return 2
    sub, rest = argv[0], argv[1:]
    try:
        if sub == "distill":
            return cmd_distill(rest)
        if sub == "confirm":
            return cmd_confirm(rest)
        if sub == "report":
            return cmd_report(rest)
        sys.stderr.write("未知子命令 %r\n%s\n" % (sub, USAGE))
        return 2
    except D.DistillError as e:
        sys.stderr.write("环境问题: %s\n" % e)
        return 2
    except D.RejectError as e:
        sys.stderr.write("REJECT: %s\n" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
