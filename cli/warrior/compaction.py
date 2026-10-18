# -*- coding: utf-8 -*-
"""检查点压缩（dsh P0 采纳②，纯函数版）。

对照 docs/research/2026-10-20-dsh-orchestration-inventory.md A 表#3/§1.5/
§⑧-2；dsh 出处 dsh-compaction-basic/lib/index.js:15-17,236-356,601。
长渗透链（多轮扫描→利用→验证）不因窗口爆掉断任务——上下文超限从终态
变可恢复态，这是漏报的第一防线。

同源三件：
  ①触发阈值= min(窗×0.8, 窗−reserved−headroom)（compaction-basic:15-17）；
  ②近尾原文保留= retain_ratio(0.16)×窗 token 逐字保留（不进摘要不改写）；
  ③摘要固定 8 节英文结构（compaction-basic:243-278 同名同序），其中
    Pending Jobs / Next Step 两节**防丢任务线索**（§⑧-2 钦点）。

纯函数律：输入=战士上下文素材（timeline 行/facts 行/简报文本），输出=
压缩包（8 节+保留尾+原文指针）；不真调 LLM——LLM 道留 **summarizer
注入位**（callable 接管 8 节改写；默认 None=确定性抽取）。同输入同输出。

素材行契约：facts 行=facts.tsv 行形（tab 或 " | " 分隔，前 6 列
id/intent/kind/target/detail/conf）；timeline 行=事件文本行；简报=多行
文本（首行兜底意图）。

接线位（等修复舰落舱后总控接 loop；loop.py/context.py 冻结中，本件零改）：
  loop.process_intent 每 turn ctx.build 之后、messages 组装前:
      used = ctx_result.estimated_tokens
      if compaction.needs_compaction(used, self.ctx.ctx_tokens):
          pkg = compaction.build_compaction(
              intent=intent_sec, briefing=ctx_result.sections["resume"],
              facts=facts_lines, timeline=timeline_tail_lines,
              window_tokens=self.ctx.ctx_tokens)
          if pkg is not None:      # 注入位：摘要+保留尾替换被遮蔽素材
              messages = [{"role": "user", "content": pkg.text
                           + "\n".join(pkg.retained_tail)}] + ...
  LLM 道：修复舰落舱后 summarizer=模型面 callable（本件默认确定性）。

与 dsh compaction-basic 对照差异声明：
  同=阈值公式/0.16 保尾/8 节固定结构/护栏「摘要必须小于被遮蔽内容」
  （:601）/摘要以 <compacted-summary> 标签+「视为既定背景」前言包裹
  （:344-356）。
  异=①dsh 摘要由 LLM 生成（summarizer 指令作为最后一条 user message，
     复用 KV cache），我方确定性抽取+原文指针，LLM 仅留注入位；
  ②dsh 摘要经 surfaceOp replace 整段落盘（审计保留事件日志），我方无
     事件日志表面层——审计由 timeline+transcript 既有面承担；
  ③dsh 供应商溢出自动恢复（prune→强制压缩→原请求重试，:861-887）属
     A 表#4（P1），不在本件范围。
"""
import re

from .context import estimate_tokens

#: dsh compaction-basic:243-278 固定 8 节（同名同序移植）
SECTIONS = (
    "Primary Request and Intent", "Key Technical Concepts",
    "Files and Code", "Errors and Fixes", "Pending Jobs",
    "Current Work", "Next Step", "Critical Context")

COMPACT_THRESHOLD_RATIO = 0.8     # 触发比（dsh :15-17）
RETAIN_RATIO = 0.16              # 近尾原文保留比（dsh retainRatio）
_FILE_KINDS = ("file", "service", "host", "endpoint", "url", "web")
_ERROR_RE = re.compile(r"fail|error|denied|超时|timeout|拦截|断路|异常",
                       re.IGNORECASE)
_PENDING_RE = re.compile(r"pending|blocked|orphan|悬空|未决|在途",
                         re.IGNORECASE)
_ERR_CAP = 5
_PENDING_CAP = 8
_FILE_CAP = 3


class CompactionRefused(ValueError):
    """护栏拒绝：摘要不小于被遮蔽内容——产包即违约（dsh :601 同律）。"""


def _flat(s, n=200):
    return " ".join(str(s).split())[:n]


def _fields(line):
    """素材行→字段列表（tab 分隔优先，次 " | "）。"""
    return (line.split("\t") if "\t" in line
            else line.split(" | "))


def _kind_of(line):
    p = _fields(line)
    if len(p) > 2:                # id/intent/kind/…（facts.tsv 行形）
        return p[2]
    if len(p) > 1:                # id/kind/…（context 折叠行形兜底）
        return p[1]
    return "?"


def threshold_tokens(window_tokens, reserved_completion=0,
                     headroom_tokens=0):
    """触发阈值：min(窗×0.8, 窗−reserved−headroom)（dsh 同公式）。"""
    w = max(1, int(window_tokens))
    return min(int(w * COMPACT_THRESHOLD_RATIO),
               w - int(reserved_completion) - int(headroom_tokens))


def needs_compaction(used_tokens, window_tokens, reserved_completion=0,
                     headroom_tokens=0):
    return used_tokens > threshold_tokens(
        window_tokens, reserved_completion, headroom_tokens)


def _split_tail(lines, window_tokens, retain_ratio):
    """从尾累积原文行直至 ≥retain_ratio×窗 token（至少 1 行）。

    返回 (head, tail)：tail 为逐字保留的近尾（字符串对象原样传递）。"""
    budget = int(max(1, int(window_tokens)) * float(retain_ratio))
    acc, cut = 0, len(lines)
    for i in range(len(lines) - 1, -1, -1):
        acc += estimate_tokens(lines[i])
        cut = i
        if acc >= budget:
            break
    return lines[:cut], lines[cut:]


def _skeleton(intent, briefing_lines, facts, timeline, head, tail):
    """确定性 8 节抽取（LLM 道的底稿——summarizer 以此为输入）。"""
    primary = intent.strip() or (briefing_lines[0] if briefing_lines
                                 else "(未提供意图行——以账本 intents.tsv 为准)")
    kinds = {}
    for l in facts:
        k = _kind_of(l)
        kinds[k] = kinds.get(k, 0) + 1
    if kinds:
        fids = [_fields(l)[0] for l in facts if _fields(l)]
        concepts = ("折叠 %d 条(kinds=%s, 窗 %s..%s)"
                    % (len(facts),
                       ",".join("%s:%d" % kv for kv in sorted(kinds.items())),
                       fids[0] if fids else "?",
                       fids[-1] if fids else "?"))
    else:
        concepts = "(压缩窗内无 facts 行)"
    file_lines = [l for l in facts if _kind_of(l) in _FILE_KINDS]
    if file_lines:
        shown = file_lines[:_FILE_CAP]
        files = "\n".join("- %s" % _flat(l) for l in shown)
        if len(file_lines) > _FILE_CAP:
            files += "\n(其余 %d 行见 facts.tsv 原文)" % (
                len(file_lines) - _FILE_CAP)
    else:
        files = "(无文件/服务类事实行)"
    errs = [l for l in timeline if _ERROR_RE.search(l)]
    errors = ("\n".join("- %s" % _flat(l) for l in errs[:_ERR_CAP])
              if errs else "(近期无错误行)")
    if len(errs) > _ERR_CAP:
        errors += "\n(另 %d 行见 timeline.tsv)" % (len(errs) - _ERR_CAP)
    pend = [l for l in timeline if _PENDING_RE.search(l)]
    pending = ("\n".join("- %s" % _flat(l) for l in pend[:_PENDING_CAP])
               if pend else "(无在途线索——以 timeline.tsv 全文为准)")
    if len(pend) > _PENDING_CAP:
        pending += "\n(另 %d 行见 timeline.tsv)" % (len(pend) - _PENDING_CAP)
    last_tl = _flat(timeline[-1]) if timeline else "(timeline 空)"
    last_fact = _flat(facts[-1]) if facts else "(facts 空)"
    current = "末事件: %s\n末事实: %s" % (last_tl, last_fact)
    nxt = ("续跑从 Pending Jobs 与 Current Work 起；断点=timeline 末行"
           "（以盘上账本为准）；下一步行动前先读账本核对在途线索。")
    critical = ("以盘上账本为准(timeline.tsv/facts.tsv/"
                "tool-executions.tsv)，别信此前叙述——摘要可能有损。"
                "\n原文指针: facts %d 行 / timeline %d 行 / 简报 %d 行；"
                "被遮蔽素材见账本原文。"
                % (len(facts), len(timeline), len(briefing_lines)))
    return {
        "Primary Request and Intent": primary,
        "Key Technical Concepts": concepts,
        "Files and Code": files,
        "Errors and Fixes": errors,
        "Pending Jobs": pending,
        "Current Work": current,
        "Next Step": nxt,
        "Critical Context": critical,
    }


class CompactionPackage(object):
    """压缩包：sections(8 节 dict)/text(渲染块)/retained_tail(近尾原文
    逐字)/shadowed_tokens(被遮蔽面)/package_tokens(摘要面)/pointers
    (原文指针)。"""

    __slots__ = ("sections", "text", "retained_tail", "shadowed_tokens",
                 "package_tokens", "pointers")

    def __init__(self, sections, text, retained_tail, shadowed_tokens,
                 package_tokens, pointers):
        self.sections = sections
        self.text = text
        self.retained_tail = retained_tail
        self.shadowed_tokens = shadowed_tokens
        self.package_tokens = package_tokens
        self.pointers = pointers


def build_compaction(intent="", briefing="", facts=(), timeline=(),
                     window_tokens=24000, reserved_completion=0,
                     headroom_tokens=0, retain_ratio=RETAIN_RATIO,
                     summarizer=None):
    """素材超阈值 → 压缩包；未超阈值 → None（零行为漂移）。

    素材拼接序（旧→新）：简报行 → facts 行 → timeline 行；近尾=最新。
    护栏：摘要 token 必须 < 被遮蔽 token，否则 CompactionRefused
    （dsh compaction-basic:601）。summarizer=LLM 注入位（callable，
    收确定性骨架 dict 返同键 dict；默认 None=确定性抽取原样）。
    """
    facts = [str(l) for l in facts]
    timeline = [str(l) for l in timeline]
    briefing_lines = [l for l in str(briefing or "").split("\n") if l]
    lines = briefing_lines + facts + timeline
    used = sum(estimate_tokens(l) for l in lines)
    if not needs_compaction(used, window_tokens, reserved_completion,
                            headroom_tokens):
        return None
    head, tail = _split_tail(lines, window_tokens, retain_ratio)
    if not head:
        return None                    # 全部落保留窗=无被遮蔽面，不产包
    sections = _skeleton(intent, briefing_lines, facts, timeline, head, tail)
    if summarizer is not None:         # LLM 道注入位（缝，不真调）
        merged = summarizer(dict(sections))
        for k in SECTIONS:
            if merged is not None and k in merged:
                sections[k] = str(merged[k])
    body = ("\n\n".join("## %s\n%s" % (k, sections[k]) for k in SECTIONS))
    text = ("<compacted-summary>\n"
            "(本摘要由检查点压缩生成——视为既定背景；"
            "原文指针见 Critical Context。)\n\n%s\n</compacted-summary>"
            % body)
    package_tokens = estimate_tokens(text)
    shadowed_tokens = sum(estimate_tokens(l) for l in head)
    if package_tokens >= shadowed_tokens:
        raise CompactionRefused(
            "摘要 %d tok ≥ 被遮蔽 %d tok——拒绝产包"
            "（dsh compaction-basic:601 护栏）" % (package_tokens,
                                                   shadowed_tokens))
    pointers = {"facts_count": len(facts), "timeline_count": len(timeline),
                "briefing_lines": len(briefing_lines),
                "shadowed_tokens": shadowed_tokens,
                "retained_lines": len(tail)}
    return CompactionPackage(sections, text, list(tail), shadowed_tokens,
                             package_tokens, pointers)
