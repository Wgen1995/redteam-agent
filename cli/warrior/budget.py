# -*- coding: utf-8 -*-
"""预算计量（W5 战士 MVP）——llmpool usage → budget.tsv 记账 + 触帽。

计量律：模型回复 usage（prompt+completion）经 budget-log 落 budget.tsv 行
（scope=意图 id，无意图=goal）；触帽（used≥cap）→ 优雅停（循环层释放当前
意图+落 stop 行——本模块只执旗，不做释放动作）。记账行写失败 fail-open：
用量照累计（预算执法不被记账故障旁路）。
"""


class BudgetMeter(object):
    """一战士进程一表：charge 累计 + exhausted 判帽。"""

    def __init__(self, ledger_io, token_cap):
        self.io = ledger_io
        self.token_cap = max(0, int(token_cap))
        self.used_tokens = 0
        self.requests = 0

    @property
    def remaining_tokens(self):
        return max(0, self.token_cap - self.used_tokens)

    def exhausted(self):
        return self.used_tokens >= self.token_cap

    def charge(self, intent_id, prompt_tokens, completion_tokens, ts,
               note=""):
        """一次模型调用入账（budget-log 既有命令，goal 锁链）。"""
        delta = int(prompt_tokens) + int(completion_tokens)
        args = {"token-delta": str(delta), "requests-delta": "1",
                "hours-delta": "0", "scope": intent_id or "goal",
                "timestamp": ts}
        if note:
            args["note"] = ("%s %s" % (self.io.warrior_id, note)).strip()
        rc, _out = self.io.write("budget-log", args)
        self.used_tokens += delta      # 记账失败亦累计（帽不可旁路）
        self.requests += 1
        return rc, self.remaining_tokens
