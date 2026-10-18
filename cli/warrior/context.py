# -*- coding: utf-8 -*-
"""上下文工程（W5 战士 MVP · 质量律 R1/R3）。

R1 一意图一脑（ARTEX 角色铁律的上下文面）：build() 无状态——每次调用从
账本行（facts/timeline）+入参（意图行/纠正信号/定向指令）全新组装；builder
不存任何跨意图缓存，聊天史绝不隐式继承。血缘走账本：本意图 facts 行 +
timeline 末行摘要（断点续跑）即全部记忆。

R3 压缩器（ARTEX Compactor cold-digest 移植，确定性版）：facts 节 token
估算超窗（ctx_tokens 减去固定节=protocol/intent 的占额）→ 冷折叠——
按文件序（=created 序）最旧的段落折叠为一行计数摘要
  [cold-digest] 折叠 N 条(kinds 计数, 时间窗 first..last)
最新 fold_keep 条逐字保留。折叠是纯函数：同输入同输出（可重放）。

token 估算：estimate_tokens(text)=ceil(len/3)——CJK 偏保守（1 token≈3 字符），
仅供窗口执法与 budget 估算；真实用量以模型 usage 回报为准入 budget.tsv。
"""
import math
import os

from . import kb_context
from . import kb_inject

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
DEFAULT_SKILL = os.path.join(REPO_ROOT, "SKILL.md")

_RESUME_LINES = 8          # 断点续跑摘要行数（timeline 末 K 行提及本意图）
_FACTS_SHARE = 0.9         # 窗口余量中 facts 可占份额（留 10% 头寸给输出）


def estimate_tokens(text):
    """确定性 token 估算（ceil(len/3)，CJK 保守）。"""
    return int(math.ceil(max(len(text), 1) / 3.0))


class ContextResult(object):
    """build() 结果：text/sections/estimated_tokens/folded/fold_digest。"""

    __slots__ = ("text", "sections", "estimated_tokens", "folded",
                 "fold_digest")

    def __init__(self, text, sections, estimated_tokens, folded, fold_digest):
        self.text = text
        self.sections = sections
        self.estimated_tokens = estimated_tokens
        self.folded = folded
        self.fold_digest = fold_digest


class ContextBuilder(object):
    """一 goal_dir 一 builder；build() 每次全新（R1：零跨意图状态）。"""

    def __init__(self, goal_dir, skill_path=None, ctx_tokens=24000,
                 fold_keep=5, resume_lines=_RESUME_LINES, kb=False,
                 kb_top_k=3, kb_dir=None, kb_inject_root=None):
        self.goal_dir = goal_dir
        self.skill_path = skill_path or DEFAULT_SKILL
        self.ctx_tokens = max(1, int(ctx_tokens))
        self.fold_keep = max(1, int(fold_keep))
        self.resume_lines = max(0, int(resume_lines))
        self.kb = bool(kb)          # 技法卡注入+SKILL 按门路由瘦身（默认关）
        self.kb_top_k = max(1, int(kb_top_k))
        self.kb_dir = kb_dir
        # W5 知识注入回路：运行时库（91 卡）按意图检索注入简报尾部（goal 配置
        # kb-inject.json 开关默认开；None=缺省 $TANYIN_HOME/knowledge）
        self.kb_inject_root = kb_inject_root

    # ---- 数据面（账本只读消费）----

    def _facts_for(self, intent_id):
        from ledger.core import Session
        rows = Session(self.goal_dir).rows("facts.tsv")
        return [r for r in rows if len(r) > 5 and r[1] == intent_id]

    def _timeline_tail(self, intent_id):
        from ledger.timeline import read_rows
        tail = []
        for r in read_rows(self.goal_dir):
            if len(r) > 3 and intent_id in r[3]:
                tail.append(r[3])
        return tail[-self.resume_lines:] if self.resume_lines else []

    # ---- 组装面 ----

    def _protocol_text(self):
        try:
            with open(self.skill_path, encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            return "(SKILL.md 不可读: %s)" % self.skill_path

    def _fact_line(self, r):
        return "%s | %s | %s | %s | conf=%s" % (r[0], r[2], r[3], r[4], r[5])

    def _fold(self, lines, budget_tokens):
        """超窗冷折叠：最旧段折叠成一行 digest，最新 fold_keep 条保留。"""
        cur = sum(estimate_tokens(l) for l in lines)
        if cur <= budget_tokens or len(lines) <= self.fold_keep:
            return lines, False, ""
        fold_n = len(lines) - self.fold_keep
        head, keep = lines[:fold_n], lines[-self.fold_keep:]
        kinds = {}
        for l in head:
            seg = l.split(" | ")
            kinds[seg[1] if len(seg) > 1 else "?"] = \
                kinds.get(seg[1] if len(seg) > 1 else "?", 0) + 1
        digest = ("[cold-digest] 折叠 %d 条冷事实(kinds=%s, 窗 %s..%s)"
                  % (fold_n, ",".join("%s:%d" % kv for kv in
                                      sorted(kinds.items())),
                     head[0].split(" | ")[0], head[-1].split(" | ")[0]))
        out = [digest] + keep
        while sum(estimate_tokens(l) for l in out) > budget_tokens \
                and len(out) > 2:
            out.pop(1)          # digest 保留，逐条收缩次新
        return out, True, digest

    def _kb_signal_text(self, iid):
        """意图关联检索的账本血缘信号（本意图 facts 行文本，末 6 行）。"""
        return " ".join("%s %s %s" % (r[2], r[3], r[4])
                        for r in self._facts_for(iid)[-6:])

    def build(self, intent, corrections=None, steers=None,
              facts_extra=None):
        """组装一意图的全新上下文（R1）。intent=dict(id/title/detail/status)。"""
        iid = intent.get("id", "")
        protocol = self._protocol_text()
        kb_sec = ""
        if self.kb:      # ② SKILL 按门路由瘦身+技法卡按意图关联注入
            protocol = kb_context.slim_skill_by_gate(
                protocol, kb_context.gate_of(self.goal_dir))
            kb_sec = kb_context.build_kb_section(
                intent, extra_text=self._kb_signal_text(iid),
                top_k=self.kb_top_k, kb_dir=self.kb_dir)
        # ③ W5 知识注入回路：运行时库 91 卡按意图（类/表面/引擎）+矩阵上下文
        # 检索，简报尾部追加「相关打法/相关避坑」节（供参考；goal 配置开关
        # 默认开；零命中零注入；活租约意图落 kb-injections.tsv 审计行）
        inj_sec = ""
        if self.kb:
            inj_sec, _sel = kb_inject.inject_briefing(
                self.goal_dir, intent, kb_root=self.kb_inject_root)
        intent_sec = "意图 %s | %s | %s | status=%s" % (
            iid, intent.get("title", ""), intent.get("detail", ""),
            intent.get("status", ""))
        facts = [self._fact_line(r) for r in self._facts_for(iid)]
        if facts_extra:
            facts = facts + list(facts_extra)
        fixed = (estimate_tokens(protocol) + estimate_tokens(intent_sec)
                 + (estimate_tokens(kb_sec) if kb_sec else 0)
                 + (estimate_tokens(inj_sec) if inj_sec else 0))
        budget = max(1, int((self.ctx_tokens - fixed) * _FACTS_SHARE))
        lines, folded, digest = self._fold(facts, budget)
        facts_sec = ("\n".join(lines) if lines
                     else "(本意图尚无 facts 行)")
        resume = self._timeline_tail(iid)
        resume_sec = ("\n".join(resume) if resume
                      else "(无断点续跑行——首跑)")
        corr = list(corrections or [])
        corr_sec = ("\n".join(corr) if corr else "(无上轮纠正信号)")
        st = list(steers or [])
        steer_sec = ("\n".join(st) if st else "(无定向指令)")
        kb_insert = (kb_sec + "\n\n") if kb_sec else ""
        text = (
            "## 协议（SKILL.md %s，禁改）\n%s\n\n"
            "## 意图\n%s\n\n"
            "%s"
            "## 相关事实（账本血缘行）\n%s\n\n"
            "## 断点续跑（timeline 末行摘要）\n%s\n\n"
            "## 上轮纠正信号\n%s\n\n"
            "## 定向指令\n%s\n\n"
            "## 任务\n执行上述意图：按协议输出 JSON 指令块"
            "（tool/ledger/done/note），完成后必报 done。"
            % (("按门路由瘦身" if self.kb else "原样"), protocol,
               intent_sec, kb_insert, facts_sec, resume_sec, corr_sec,
               steer_sec))
        if inj_sec:      # 简报尾部追加知识注入节（任务节之后=情报附录）
            text = text + "\n\n" + inj_sec
        sections = {"protocol": protocol, "intent": intent_sec,
                    "facts": facts_sec, "resume": resume_sec,
                    "corrections": corr_sec, "steers": steer_sec}
        if self.kb:
            sections["kb"] = kb_sec
        if inj_sec:
            sections["kb_inject"] = inj_sec
        return ContextResult(text, sections, estimate_tokens(text), folded,
                             digest)
