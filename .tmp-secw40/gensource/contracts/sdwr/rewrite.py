import sys
from pathlib import Path

_CONTRACTS = str(Path(__file__).resolve().parent.parent)
if _CONTRACTS not in sys.path:
    sys.path.insert(0, _CONTRACTS)

from sdwr.worklist import _band, HIGH_RISK_BANDS


def _ok(fact):
    return bool(fact.get("confirmed")) and bool(str(fact.get("evidence") or "").strip())


def _is_high_risk(card):
    """高危 sink（band 0/1：反序列化/SQL注入/XXE/越权/命令执行/文件穿越/XSS/SSTI/SSRF 等）：
    这类 sink 的 intended/uncontrolled 类级消卡只信任
    source_role=analyzer 的事实（真做过五步验证），不信任 Summarizer 的粗粒度类级猜测
    （一旦猜错，这张卡永久关闭，Analyzer 再也不会看它，等于把真实漏洞埋进"类级剪枝"里）。
    这不是禁止高危 sink 被级联消卡，而是把"谁有资格下这个判断"的门槛提高到"亲自验证过
    代表实例的 Analyzer"——Analyzer 分析一个高危代表实例得出的 intended/uncontrolled
    结论，依然可以按"聚簇：代表实例五步+兄弟实例结构一致性"去消掉同类的兄弟卡，不浪费。
    低危噪音类（band 2，如格式化字符串/弱加密参数）不受此限制，Summarizer 的类级判断
    可以直接生效，因为这类 sink 本身价值密度低，效率优化的收益远大于误判风险。"""
    return _band(card.get("sink_type")) in HIGH_RISK_BANDS


def _reason(prefix, fact):
    """reason 统一格式：<前缀> + 可选 :fact=<fact_id>——fact_id 缺失时
    退化为纯前缀（兼容未带 fact_id 的旧调用/单元测试），带 fact_id 时可供 D2 retract
    按 fact_id 精确反查该事实消掉了哪些卡（同名函数被多条不同 fact 确认时不再混淆）。"""
    fid = fact.get("fact_id")
    return "%s:fact=%s" % (prefix, fid) if fid else prefix


def apply_rewrite(cards, facts):
    patches = []
    for card in cards:
        cid = card["card_id"]
        high_risk = _is_high_risk(card)
        for fact in facts:
            if not _ok(fact):
                continue
            t = fact["type"]
            if t == "uncontrolled":
                # 高危 sink 的 uncontrolled 只信任 Analyzer 真做过五步验证后写的事实
                # （source_role=analyzer）——Summarizer 的粗粒度类级猜测（缺失 source_role
                # 也按此对待，安全默认）依然挡住；这不是浪费 Analyzer 的结论，恰恰是让它的
                # 结论能力所能及地去消掉结构相同的兄弟卡（聚簇：代表实例五步+兄弟结构一致性）。
                if high_risk and fact.get("source_role") != "analyzer":
                    continue
                ets = card.get("entry_types") or []
                if ets and all(e == fact["scope"] for e in ets):
                    patches.append({"card_id": cid, "terminal_state": "disproved", "reason": _reason("uncontrolled:" + fact["scope"], fact)})
                    break
            if t == "intended":
                # 同上：高危 sink 的 intended 只信任 Analyzer 亲自验证过的结论。
                if high_risk and fact.get("source_role") != "analyzer":
                    continue
                if card.get("component") == fact["component"] and card.get("sink_type") == fact["sink_type"] and not card.get("has_bypass"):
                    patches.append({"card_id": cid, "terminal_state": "not_applicable", "reason": _reason("intended:" + fact["component"], fact)})
                    break
            if t == "kills":
                mt = card.get("must_through")
                if mt and fact["function"] in mt and card.get("sink_type") == fact["sink_type"]:
                    patches.append({"card_id": cid, "terminal_state": "blocked_at", "blocked_at": fact["function"], "reason": _reason("kills:" + fact["function"], fact)})
                    break
            if t == "dead" and card.get("sink_id") == fact.get("sink_id"):
                patches.append({"card_id": cid, "terminal_state": "not_applicable", "reason": _reason("dead", fact)})
                break
            if t == "no_edge":
                only = card.get("only_via") or []
                if (fact["src"], fact["dst"]) in only and not card.get("has_alt_path"):
                    patches.append({"card_id": cid, "terminal_state": "no_path", "reason": _reason("no_edge", fact)})
                    break
    return patches
