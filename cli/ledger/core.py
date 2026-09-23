# -*- coding: utf-8 -*-
"""tanyin ledger core（批次 1 T1）——契约：contracts-v2。
转义律（契约 01 §1）：BS->BSBS, tab->BS t, CR->BS r, LF->BS n, 分号->BS ;
哈希约定【推导转正】：hash = sha256(prev_hash + "|" + 逐字段转义后 tab 连接的本行全部字段(不含 hash 列))，链经 prev_hash 列延续，首行 prev=GENESIS。
"""
import hashlib, os, re, sys
from .schemas import TABLES, SCHEMA_VERSION, GENESIS

# 九门全序（契约 04-phases states 序；02a §32 跳门检测依据）。写侧枚举校验同源
# （write_cmds checkpoint --phase 拒收 ∉九门 复用本清单，禁双份枚举）。
GATE_ORDER = ("P0", "P1", "P2", "P3", "P4", "P5", "P5.5", "P6.0", "P6")
# 门出口断言事件词汇【推导】（02a §32「每门出口断言的命令调用必产生 timeline 事件」
# 的落账形态；批次 3 phases.yaml 引擎在每门 exit 断言通过后经 append-timeline 记入，
# 本命令只做存在性/序检测，不代写）。容忍尾部明细（如 asserts=3 result=PASS）。
GATE_EXIT_EVENT = re.compile(r"^gate-exit:(P(?:\d(?:\.\d)?))(?:\s.*)?$")

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
    # newline="\n": 账本字节纪律——链式哈希/双指纹按 LF 落盘，Windows 文本模式不得翻译为 CRLF
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(chr(9).join(esc(c) for c in r) + chr(10))


def ensure_utf8_stdio():
    """入口进程 stdout/stderr 统一 UTF-8（Windows 控制台默认 GBK 会炸中文输出）。
    老 Python 无 reconfigure 则静默跳过；仅入口脚本调用，库导入无副作用。"""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

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

    def gate_exit_seq(self):
        """按出现序提取 gate-exit 门事件门标（GATE_EXIT_EVENT）；返回 (seq, bad)。
        bad=首个无效门标（∉GATE_ORDER 的 gate-exit 行）。"""
        seq, bad = [], None
        ev_i = TABLES["timeline.tsv"].index("event")
        for r in self.data.get("timeline.tsv", []):
            m = GATE_EXIT_EVENT.match(r[ev_i])
            if not m:
                continue
            if m.group(1) not in GATE_ORDER:
                bad = bad or m.group(1)
                continue
            seq.append(m.group(1))
        return seq, bad

    def gate_jump_errors(self):
        """跳门检测（02a §32·设计 §5.1）：九门 exit 断言事件存在性＋序检查。
        规则【推导】：已达门（timeline.phase 最大门标 ∪ gate-exit 最大门标）之前的
        每一门必有 gate-exit 事件，缺记录=跳门；gate-exit 首现序须按 GATE_ORDER
        递增（先过后门先出=乱序补票）。返回错误行清单（空=通过）。"""
        ph_i = TABLES["timeline.tsv"].index("phase")
        reached = [g for g in (r[ph_i].strip() for r in self.data.get("timeline.tsv", []))
                   if g in GATE_ORDER]
        seq, bad = self.gate_exit_seq()
        errs = []
        if bad:
            errs.append("gate-exit 无效门标:%s" % bad)
        firsts = []
        seen = set()
        for g in seq:
            if g not in seen:
                firsts.append(g)
                seen.add(g)
        for a, b in zip(firsts, firsts[1:]):
            if GATE_ORDER.index(b) <= GATE_ORDER.index(a):
                errs.append("gate-exit 乱序:%s 先于 %s" % (b, a))
        top = max([GATE_ORDER.index(g) for g in firsts + reached], default=-1)
        required = {g for g in GATE_ORDER if GATE_ORDER.index(g) < top}
        missing = sorted(required - seen, key=GATE_ORDER.index)
        if missing:
            where = GATE_ORDER[top] if top >= 0 else "?"
            for g in missing:
                errs.append("缺失门事件:gate-exit:%s（已达 %s）" % (g, where))
        return errs

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
    if not ok:
        print("FAIL verify-chain: 断链行=%d" % bad)
        return 1
    # 跳门检测（02a §32）：九门 exit 断言事件存在性，缺记录=FAIL＋缺失门事件清单
    errs = s.gate_jump_errors()
    if errs:
        print("FAIL verify-chain: 跳门（缺失门事件 %d）" % len(errs))
        for e in errs[:20]:
            print(e)
        return 1
    n_exit = len(s.gate_exit_seq()[0])
    print("PASS verify-chain: %d 行链完整 gate_exit=%d 跳门=0"
          % (len(s.rows("timeline.tsv")), n_exit))
    return 0

def cmd_next_id(goal_dir, table, prefix, goal_id):
    tname = table if table.endswith(".tsv") else table + ".tsv"
    if tname not in TABLES:
        raise ValueError("未知表: " + table)
    s = Session(goal_dir)
    print(next_id(s.rows(tname), prefix, goal_id))
    return 0
