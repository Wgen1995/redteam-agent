# -*- coding: utf-8 -*-
"""C2 域账本存储——append-only 哈希链 + 行族投影。

机制律（timeline.py O(1) 尾追加同律，简化版——C2 表行量<<timeline，
但同款纪律：goal 锁内「尾读末行 hash → 单行追加落盘 fsync」，零整表重写）：
- append(table, fields): 取 goal_lock → 读该表末行 prev_hash →
  core.row_hash 算新行 → 单行 append+fsync（字节=core.esc 同律）；
- read(table): 全量读（投影/审计面；列数错=fail-closed ValueError）；
- verify_chains(): 逐表逐行重算链，篡改=首坏行号（防抵赖：beacon 改心跳/
  指令改载荷/审批改决定=断链可检）；
- projection 同 id/同键最新行胜——行只增不改，状态=投影非列值。

单写者纪律：C2 表与 13 表共用 <goal-dir>/.lock（filelock.goal_lock 单源），
C2 追加与 ledger 写路径互斥，无双写者。
"""
import os

from ..ledger import core
from ..ledger.filelock import goal_lock
from .tables import C2_DIRNAME, C2_TABLES, cols

_HASH = "hash"


class C2Error(Exception):
    """C2 面业务拒绝（REJECT 律：不行+为什么+怎么走由调用方拼改道提示）。"""


class C2Store:
    """一个 goal 的 C2 域账本句柄（读面零锁；写面 append 自取 goal 锁）。"""

    def __init__(self, goal_dir):
        self.goal_dir = goal_dir
        self.dir = os.path.join(goal_dir, C2_DIRNAME)

    def path(self, table):
        return os.path.join(self.dir, table)

    # ---- 读面 ----
    def read(self, table):
        """全量行；缺表=[]。列数坏=fail-closed（core.read_tsv 同判据）。"""
        cols(table)
        p = self.path(table)
        if not os.path.exists(p):
            return []
        return core.read_tsv(p, len(C2_TABLES[table]))

    def read_numbered(self, table):
        """[(行号, 行)]——行号=物理行序（append-only 下稳定=游标域）。"""
        return list(enumerate(self.read(table), 1))

    def latest_by_key(self, table, key_index=0):
        """行族投影：同 key（默认 id 列）最新行胜 -> {key: row}。"""
        out = {}
        for r in self.read(table):
            out[r[key_index]] = r
        return out

    def next_id(self, table, prefix):
        """{前缀}-{goal_id}-{四位序号}（core.next_id 同律，C2 表内独立序域）。"""
        gid = os.path.basename(os.path.normpath(self.goal_dir)).replace("G-", "", 1)
        return core.next_id(self.read(table), prefix, gid)

    # ---- 写面（O(1) 尾追加）----
    def append(self, table, fields):
        """追加一行（goal 锁内尾读→链算→单行落盘 fsync）；返回新行列表。

        fields=除 prev_hash/hash 外全字段（缺列 ValueError 拒收——缺字段
        不得静默空串）。行只增不改：任何「更新」=追加新行+投影取最新。
        """
        c = cols(table)
        body = [k for k in c if k not in ("prev_hash", _HASH)]
        missing = [k for k in body if k not in fields]
        if missing:
            raise ValueError("%s 缺字段: %s" % (table, " ".join(missing)))
        with goal_lock(self.goal_dir):
            os.makedirs(self.dir, exist_ok=True)
            prev = self._tail_prev(table)
            vals = dict(fields)
            row = []
            for k in c:
                if k == "prev_hash":
                    row.append(prev)
                elif k == _HASH:
                    row.append("")            # 先占位，链算后回填
                else:
                    row.append(str(vals[k]))
            # 回填 hash：payload=除 hash 列外全字段（含 prev_hash）
            hi = c.index(_HASH)
            row[hi] = core.row_hash(prev, row[:hi] + row[hi + 1:])
            line = chr(9).join(core.esc(v) for v in row)
            with open(self.path(table), "a", encoding="utf-8", newline="\n") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())
        return row

    def _tail_prev(self, table):
        """末行 hash（链 prev）；空/缺表=GENESIS。"""
        rows = self.read(table)
        if not rows:
            return core.GENESIS
        return rows[-1][cols(table).index(_HASH)]

    # ---- 链校验 ----
    def verify_chains(self):
        """逐表重算链；返回 {表: 首坏行号(0=完整)}。篡改任何 C2 行=可检。"""
        out = {}
        for t, c in C2_TABLES.items():
            prev = core.GENESIS
            bad = 0
            hi = c.index(_HASH)
            for i, r in enumerate(self.read(t), 1):
                if len(r) != len(c):
                    bad = i
                    break
                if r[c.index("prev_hash")] != prev:
                    bad = i
                    break
                if core.row_hash(prev, r[:hi] + r[hi + 1:]) != r[hi]:
                    bad = i
                    break
                prev = r[hi]
            out[t] = bad
        return out
