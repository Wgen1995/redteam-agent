# -*- coding: utf-8 -*-
"""账本消费层（W5 战士 MVP）——战士对账本的全部读写面。

零复制律：写命令全经 ledger.registry.lookup（goal 写锁+既有校验执法链），
绝不绕锁私铸 TSV 行；租约/prereq 解析单源引 ledger.write_cmds（P0-2 租约
与 v0.8 链基件的同款函数，不抄第二实现）；timeline 事件行经
ledger.timeline.append_tl_locked（llmpool_wire/gate 同款基础设施单源写方，
actor=warrior:<id>）。

R2 串行链（质量律）：claimable_intents 只列 pending 且（无 prereq 或
prereq 已终态）的意图——链不前置倾倒，逐个进 frontier。
"""
import contextlib
import io

from ledger import registry
from ledger.timeline import append_tl_locked
from ledger.write_cmds import (_INTENT_TERMINAL, _prereq_of,
                               lease_of_detail, parse_wall_ts)

_TERMINAL = _INTENT_TERMINAL
_DETAIL, _STATUS, _PRIORITY = "detail", "status", "priority"


def _intent_dict(row, cols):
    return {c: row[i] for i, c in enumerate(cols)}


class LedgerIO(object):
    """一 goal_dir × 一战士身份。全部方法消费不改账本结构。"""

    def __init__(self, goal_dir, warrior_id):
        self.goal_dir = goal_dir
        self.warrior_id = warrior_id
        from ledger.core import TABLES
        self._intent_cols = list(TABLES["intents.tsv"])

    # ---- 读面 ----

    def _ctx(self):
        from ledger.write_cmds import Ctx
        return Ctx(self.goal_dir)

    def latest_intents(self):
        """intents 最新行映射（事件溯源：文件序后者覆盖前者）→ dict 列表。"""
        ctx = self._ctx()
        latest = {}
        for r in ctx.rows("intents.tsv"):
            latest[r[0]] = r
        return [_intent_dict(row, self._intent_cols)
                for _, row in sorted(latest.items())]

    def claimable_intents(self):
        """pending 且 prereq 终态（R2 frontier）；priority 降序、id 升序。"""
        latest = {i["id"]: i for i in self.latest_intents()}
        out = []
        for i in latest.values():
            if i[_STATUS] != "pending":
                continue
            pr = _prereq_of(i.get(_DETAIL, ""))
            if pr:
                p = latest.get(pr)
                if p is None or p[_STATUS] not in _TERMINAL:
                    continue
            try:
                pri = float(i.get(_PRIORITY) or 0.0)
            except ValueError:
                pri = 0.0
            out.append((pri, i["id"], i))
        out.sort(key=lambda t: (-t[0], t[1]))
        return [i for _, _, i in out]

    def owner_of(self, iid):
        """最新行 detail → (owner, 到期钟文本)。"""
        for i in self.latest_intents():
            if i["id"] == iid:
                return lease_of_detail(i.get(_DETAIL, ""))
        return ("", "")

    def holds(self, iid, ts):
        """租约持有判定：最新行 active 且 owner=我 且租约未过期。"""
        for i in self.latest_intents():
            if i["id"] != iid:
                continue
            if i[_STATUS] != "active":
                return False
            owner, expiry = lease_of_detail(i.get(_DETAIL, ""))
            if owner != self.warrior_id:
                return False
            return parse_wall_ts(expiry) is not None \
                and parse_wall_ts(ts) is not None \
                and parse_wall_ts(expiry) > parse_wall_ts(ts)
        return False

    def my_active_intents(self, ts):
        """我持有的活租约意图（断点续跑/重生接管面）。"""
        out = []
        for i in self.latest_intents():
            if i[_STATUS] == "active" \
                    and self.holds(i["id"], ts):
                out.append(i)
        return out

    # ---- 写面（全经既有锁+执法链）----

    def _run(self, cmd, args):
        h = registry.lookup(cmd)
        if h is None:
            return 2, "未知命令: " + cmd
        rest = ["--%s=%s" % (k, v) for k, v in args.items()]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), \
                contextlib.redirect_stderr(buf):
            try:
                rc = h(self.goal_dir, rest)
            except Exception as e:              # noqa: BLE001
                return 1, "FAIL %s" % e
        return rc, buf.getvalue()

    def write(self, cmd, args):
        """通用写命令（协议 ledger 指令的执行面）。返回 (rc, out)。"""
        return self._run(cmd, args)

    def claim(self, iid, lease_min, ts):
        ok, out = self._run("set-intent-status", {
            "id": iid, "status": "active", "owner": self.warrior_id,
            "lease-min": str(int(lease_min)), "timestamp": ts})
        return ok == 0, out.strip()

    def complete(self, iid, ts, reason=""):
        args = {"id": iid, "status": "done", "timestamp": ts}
        if reason:
            args["reason"] = reason
        ok, out = self._run("set-intent-status", args)
        return ok == 0, out.strip()

    def block(self, iid, ts, reason):
        ok, out = self._run("set-intent-status", {
            "id": iid, "status": "blocked", "reason": reason,
            "timestamp": ts})
        return ok == 0, out.strip()

    # ---- timeline（基础设施单源写方先例）----

    def add_tl(self, event, ts, phase="P3"):
        append_tl_locked(self.goal_dir, ts, event, actor=self.warrior_id,
                         phase=phase)
