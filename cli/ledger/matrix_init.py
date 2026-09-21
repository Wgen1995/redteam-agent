# -*- coding: utf-8 -*-
"""matrix-init〔特殊 1/1，契约 02 §4/02a §37〕——P1 门：矩阵基线铸造。

列（vuln_class）从 VOCAB 钉死（WSTG v4.2 版本化，shared/VOCAB.md）；行（attack_surface）
默认取 assets.tsv in_scope 清单，可 --surfaces 覆盖【02a §37 推导】。生成 matrix.tsv 长表
全行 state=空（未检查——终态门禁分母：空必须消灭），schema_version=2，frozen_at 空
（锚点冻结走 matrix-freeze）。写前拒收：矩阵已初始化 / 无攻击面 / vocab 缺失(exit 2)。
成功=matrix 行落账+timeline 链式事件。退出码 0/1/2。
"""
import hashlib, os

from . import core
from .schemas import TABLES
from .query_cmds import parse_kv, UsageError, usage_guard

DEFAULT_VOCAB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared", "VOCAB.md")


def _load_vocab(vocab_arg):
    path = vocab_arg or DEFAULT_VOCAB
    if not os.path.exists(path):
        raise UsageError("vocab 未找到: " + path + "（--vocab=<路径> 或建 shared/VOCAB.md）")
    classes, ver = [], ""
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("version:"):
                ver = line.split(":", 1)[1].strip()
            elif line.startswith("- "):
                c = line[2:].strip().split()[0]
                if c and c not in classes:
                    classes.append(c)
    if not classes:
        raise UsageError("vocab 无有效条目: " + path)
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()[:12]
    return classes, ver or "unversioned", sha


def run_matrix_init(goal_dir, rest):
    kv, flags = parse_kv(rest)
    for k in kv:
        if k not in ("timestamp", "vocab", "surfaces"):
            raise UsageError("matrix-init 未知参数: " + k)
    ts = kv.get("timestamp", "")
    if not ts:
        raise UsageError("matrix-init 必填 --timestamp=<ISO8601>")
    s = core.Session(goal_dir)
    if s.rows("matrix.tsv"):
        print("REJECT\tmatrix-init\tmatrix 已初始化（基线不可重建，修订走 matrix-set/matrix-freeze）")
        return 1
    af = TABLES["assets.tsv"]
    in_scope_idx = af.index("in_scope")
    value_idx = af.index("value")
    if "surfaces" in kv:
        surfaces = [x for x in kv["surfaces"].split(";") if x]
    else:
        surfaces = [r[value_idx] for r in s.rows("assets.tsv") if r[in_scope_idx] in ("in_scope", "1")]
    if not surfaces:
        print("REJECT\tmatrix-init\t无 in_scope 攻击面（先 add-asset 或 --surfaces=显式清单）")
        return 1
    classes, ver, sha = _load_vocab(kv.get("vocab", ""))
    mf = TABLES["matrix.tsv"]
    mi = {f: i for i, f in enumerate(mf)}
    new_rows = []
    for surf in surfaces:
        for vc in classes:
            new_rows.append([surf if f == "attack_surface" else vc if f == "vuln_class" else ts if f == "updated" else "2" if f == "schema_version" else "" for f in mf])
    # 全量校验后写入（写前拒收纪律）：先 timeline 后 matrix 与写组一致
    core.write_tsv(os.path.join(goal_dir, "matrix.tsv"), s.rows("matrix.tsv") + new_rows)
    tl_path = os.path.join(goal_dir, "timeline.tsv")
    tl_rows = s.rows("timeline.tsv")
    ph = TABLES["timeline.tsv"].index("hash")
    prev = tl_rows[-1][ph] if tl_rows else core.GENESIS
    event = "matrix-init vocab=%s sha=%s surfaces=%d classes=%d" % (ver, sha, len(surfaces), len(classes))
    wo = [ts, "CLI", "P1", event, "", prev, "2"]
    h = core.row_hash(prev, wo)
    tlf = TABLES["timeline.tsv"]
    tl_rows.append([wo[0], wo[1], wo[2], wo[3], wo[4], prev, h, "2"])
    core.write_tsv(tl_path, tl_rows)
    print("PASS\tmatrix-init\trows=%d surfaces=%d classes=%d vocab=%s@%s" % (len(new_rows), len(surfaces), len(classes), ver, sha))
    return 0


HANDLERS = {"matrix-init": usage_guard(run_matrix_init)}
