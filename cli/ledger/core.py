# -*- coding: utf-8 -*-
"""tanyin ledger core（批次 1 T1）——契约：contracts-v2。
转义律（契约 01 §1）：BS->BSBS, tab->BS t, CR->BS r, LF->BS n, 分号->BS ;
哈希约定【推导转正】：hash = sha256(prev_hash + "|" + 逐字段转义后 tab 连接的本行全部字段(不含 hash 列))，链经 prev_hash 列延续，首行 prev=GENESIS。
"""
import hashlib, os, re, sys
from .schemas import TABLES, SCHEMA_VERSION, GENESIS

BS = chr(92)
_ESC = {BS: BS + BS, chr(9): BS + "t", chr(13): BS + "r", chr(10): BS + "n", ";": BS + ";"}
_UN = {BS + "t": chr(9), BS + "r": chr(13), BS + "n": chr(10), BS + ";": ";", BS + BS: BS}

def esc(s):
    return "".join(_ESC.get(c, c) for c in str(s))

def unesc(s):
    out, i, n = [], 0, len(s)
    while i < n:
        if s[i] == BS and i + 1 < n:
            pair = s[i:i+2]
            out.append(_UN.get(pair, pair))
            i += 2
        else:
            out.append(s[i]); i += 1
    return "".join(out)

def row_hash(prev, fields_wo_hash):
    payload = prev + "|" + chr(9).join(esc(c) for c in fields_wo_hash)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def read_tsv(path, nfields):
    rows = []
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.rstrip(chr(10))
            if not line.strip():
                continue
            cells = [unesc(c) for c in line.split(chr(9))]
            if len(cells) != nfields:
                raise ValueError("列数错误 %s:%d %d!=%d" % (path, ln, len(cells), nfields))
            rows.append(cells)
    return rows

def write_tsv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(chr(9).join(esc(c) for c in r) + chr(10))

PREFIX = {"goals": "G", "scope": "S", "intents": "INT", "facts": "F", "findings": "FD",
          "assets": "AST", "edges": "E", "approvals": "AP", "E-index": "EV",
          "matrix": None, "timeline": None, "budget": None, "creds": "CRED"}

def next_id(rows, prefix, goal_id):
    """{前缀}-{goal-id}-{四位序号}，定宽零填充；由 ledger-next-id 原子分配。"""
    best = 0
    pat = re.compile("^" + prefix + "-" + re.escape(goal_id) + "-([0-9]{4})$")
    for r in rows:
        m = pat.match(r[0])
        if m:
            best = max(best, int(m.group(1)))
    return "%s-%s-%04d" % (prefix, goal_id, best + 1)

class Session:
    """单 goal 交战区：sessions/<goal-id>/ 下 13 表加载与校验。"""
    def __init__(self, goal_dir):
        self.dir = goal_dir
        self.goal_id = os.path.basename(os.path.normpath(goal_dir)).replace("G-", "", 1) if os.path.isdir(goal_dir) else "g1"
        self.data = {}
        for tname, fields in TABLES.items():
            p = os.path.join(goal_dir, tname)
            self.data[tname] = read_tsv(p, len(fields)) if os.path.exists(p) else []

    def rows(self, tname):
        return self.data[tname]

    def verify_chain(self):
        """timeline 链式哈希逐行重算；返回 (ok, first_bad_line)。"""
        rows = self.data.get("timeline.tsv", [])
        prev = GENESIS
        for i, r in enumerate(rows, 1):
            f = dict(zip(TABLES["timeline.tsv"], r))
            if f.get("prev_hash") != prev:
                return False, i
            wo = [r[j] for j in range(len(TABLES["timeline.tsv"])) if TABLES["timeline.tsv"][j] != "hash"]
            if row_hash(prev, wo) != f.get("hash"):
                return False, i
            prev = f["hash"]
        return True, 0

    def validate(self):
        """列数（read_tsv 已保证）+ schema_version + 链完整性 + 引用闭合（v1 范围：timeline/intents 引用）。"""
        errs = []
        for tname, fields in TABLES.items():
            if "schema_version" in fields:
                idx = fields.index("schema_version")
                for i, r in enumerate(self.data[tname], 1):
                    if idx < len(r) and r[idx] != SCHEMA_VERSION:
                        errs.append("%s:%d schema_version!=2" % (tname, i))
        ok, bad = self.verify_chain()
        if not ok:
            errs.append("timeline 链断裂于第 %d 行" % bad)
        return errs

def cmd_validate(goal_dir):
    s = Session(goal_dir)
    errs = s.validate()
    if errs:
        for e in errs:
            print("FAIL " + e)
        return 1
    print("PASS validate: 13 表列数/schema_version/链完整")
    return 0

def cmd_verify_chain(goal_dir):
    s = Session(goal_dir)
    ok, bad = s.verify_chain()
    print(("PASS verify-chain: %d 行链完整" % len(s.rows("timeline.tsv"))) if ok else ("FAIL verify-chain: 断裂于第 %d 行" % bad))
    return 0 if ok else 1

def cmd_next_id(goal_dir, table, prefix, goal_id):
    tname = table if table.endswith(".tsv") else table + ".tsv"
    if tname not in TABLES:
        raise ValueError("未知表: " + table)
    s = Session(goal_dir)
    print(next_id(s.rows(tname), prefix, goal_id))
    return 0
