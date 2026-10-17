# -*- coding: utf-8 -*-
"""timeline 铸造单源（批次 10 T5 起源；W2 01P0-1+02P0 整文件重写）——O(1) 尾追加+epoch 撕裂读封口。

前科（05-engineering-debt ②/建议1、exceed-review 02 骂1/骂2，F2 排队三评审周期）：
append_tl_locked 每事件「Session 全量载 13 表→write_tsv 整表重写」=单事件 O(N)
写+解析，N 事件 O(N²)（实测 3000 行尾窗单事件 ~65ms 劣化在案）；读侧无一致性
校验=追加窗口读者可见半行（撕裂快照）——v1.0b 多战士并发写+webui 常驻读的自爆雷。

契约（v1.0b 门票，ts 必填律不变——EPOCH/墙钟缺省全数退役）：
- chained_row(rows, ts, actor, phase, event, revert='') 纯函数不变——算 (新行, prev)，
  调用方自持锁/会话时用（check_cmds 形态）；
- append_tl_locked(gd, ts, event, actor, phase, revert='')：goal 锁内「O(1) 尾读末行
  →单行追加落盘（fsync）→epoch 戳原子递增」。timeline.tsv 仍是唯一事实源（AI 直读
  TSV 产品律）：追加行字节=write_tsv 同律（esc+tab+LF），与整表重写路径（Ctx.commit
  形态）交错接链互通，字节级零漂移（金样/fingerprint/链哈希之根）。末行撕裂/列数坏
  =fail-closed 拒追加零半写——旧路径对无 LF 收尾末行会静默"修复"入链，新路径拒写，
  修复走人工（撕裂态先走恢复协议，P0.md 同律）；
- .timeline.epoch（dot 工件，.lock 同律：不进 13 表，金样/指纹/链哈希零干扰）：每次
  成功追加原子递增一世；read_rows 读前后双验 epoch——窗内有追加=整体重读，持续变更
  =TornTimelineError 拒绝返回（读时一致性校验封口，不吐撕裂视图）。epoch=读一致性戳
  非事实源（真相在 timeline.tsv+fsync），故递增免 fsync、损坏按 0 世处理。
"""
import os

from . import core
from .schemas import TABLES
from .filelock import goal_lock

_HASH_IDX = TABLES["timeline.tsv"].index("hash")
_NCOL = len(TABLES["timeline.tsv"])
_EPOCH_NAME = ".timeline.epoch"
_TAIL_WINDOW = 8192      # 尾读窗口：单行超窗则逐窗回退，复杂度仍 O(行长)
_RETRY = 8               # read_rows 一致性重试上限（耗尽=fail-closed）


class TornTimelineError(RuntimeError):
    """撕裂视图/torn 末行——fail-closed 拒绝（读不吐混读，写零半写）。"""


def chained_row(rows, ts, actor, phase, event, revert=""):
    """算链新行——返回 (row, prev)；row 8 列含 hash。"""
    if not ts:
        raise TypeError("ts 必填——EPOCH/墙钟缺省已退役（批次 10 P2#9）")
    prev = rows[-1][_HASH_IDX] if rows else core.GENESIS
    wo = [ts, actor, phase, event, revert, prev, "2"]
    return [ts, actor, phase, event, revert, prev,
            core.row_hash(prev, wo), "2"], prev


def _tail_bytes(path):
    """O(1) 尾读：只碰文件尾窗，返回 (末行字节或 None, 末字节是否 LF, 文件大小)。

    与 read_tsv 同语义：跳过尾随空行取最后一个非空行。文件缺/空=(None, True, 0)。
    """
    try:
        f = open(path, "rb")
    except FileNotFoundError:
        return None, True, 0
    with f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        if size == 0:
            return None, True, 0
        f.seek(size - 1)
        last_b = f.read(1)
        pos, buf = size, b""
        while pos > 0:
            step = min(_TAIL_WINDOW, pos)
            pos -= step
            f.seek(pos)
            buf = f.read(step) + buf
            body = buf.rstrip(b"\n")
            if body:
                cut = body.rfind(b"\n")
                if cut != -1:
                    return body[cut + 1:], last_b == b"\n", size
                # 窗内无行界——真·单行文件到头，或行首在更早窗：pos==0 才是前者
                if pos == 0:
                    return body, last_b == b"\n", size
        return None, last_b == b"\n", size   # 全空行文件：无有效末行


def _last_row(path):
    """末行解析为 8 列行；缺/空文件=None。撕裂尾/列数坏=fail-closed（read_tsv 同判据）。"""
    raw, ends_lf, size = _tail_bytes(path)
    if raw is None:
        if size > 0:
            raise TornTimelineError(
                "timeline.tsv 仅含空行（非 write_tsv 产物）——拒追加，先人工修复: " + path)
        return None
    if not ends_lf:
        raise TornTimelineError(
            "timeline.tsv 末行无 LF 收尾（追加窗半行/损坏）——fail-closed 拒追加"
            "（撕裂态先走恢复协议）: " + path)
    cells = [core.unesc(c) for c in raw.decode("utf-8").split(chr(9))]
    if len(cells) != _NCOL:
        raise ValueError("列数错误 %s:末行 %d!=%d" % (path, len(cells), _NCOL))
    return cells


def _read_epoch(gd):
    """当前世代号（int）。缺戳/损坏=0 世（epoch=读一致性戳，非事实源，宽容降读）。"""
    try:
        with open(os.path.join(gd, _EPOCH_NAME), encoding="utf-8") as f:
            return int(f.read().strip() or "0")
    except (OSError, ValueError):
        return 0


def _bump_epoch(gd):
    """世代+1 原子换入（tmp+os.replace，免 fsync：账本真相在 timeline.tsv 追加+fsync）。"""
    p = os.path.join(gd, _EPOCH_NAME)
    tmp = p + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(str(_read_epoch(gd) + 1) + chr(10))
        os.replace(tmp, p)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return _read_epoch(gd)


def read_rows(gd, attempts=_RETRY):
    """读路径投影（=timeline.tsv 全量行）+ 读时 epoch 一致性校验（撕裂封口）。

    每次尝试：验世代→全量读→再验世代；两验一致才返回。窗内有追加（世代变）或
    末行暂不可解析（追加窗半行）=整体重读；重试耗尽仍不一致=TornTimelineError
    拒绝返回（不吐撕裂快照）。无并发介入的持久损坏=read_tsv 原语义 ValueError 直抛。
    """
    p = os.path.join(gd, "timeline.tsv")
    for _ in range(max(1, attempts)):
        e1 = _read_epoch(gd)
        try:
            rows = core.read_tsv(p, _NCOL) if os.path.exists(p) else []
            err = None
        except ValueError as e:
            rows, err = None, e
        e2 = _read_epoch(gd)
        if err is not None:
            if e1 == e2:
                raise err                     # 非并发所致——持久损坏，原语义直抛
            continue                          # 追加窗半行——整体重读
        if e1 == e2:
            return rows
    raise TornTimelineError(
        "epoch 读窗内持续变更——撕裂快照拒绝返回（重试 %d 次耗尽，fail-closed）"
        % max(1, attempts))


def append_tl_locked(gd, ts, event, actor, phase, revert=""):
    """goal 锁包「O(1) 尾读末行→单行追加→epoch 递增」——万行级账本单事件常数耗时。

    追加字节=write_tsv 同律（esc+tab+LF）；fsync 保 kill -9（追加行要么全在要么
    全无，链经 prev_hash 延续不变）。末行撕裂/列数坏=拒追加零半写（fail-closed）。
    """
    if not ts:
        raise TypeError("ts 必填——EPOCH/墙钟缺省已退役（批次 10 P2#9）")
    p = os.path.join(gd, "timeline.tsv")
    with goal_lock(gd):
        last = _last_row(p)
        row, _ = chained_row([last] if last else [], ts, actor, phase, event, revert)
        line = (chr(9).join(core.esc(c) for c in row) + chr(10)).encode("utf-8")
        with open(p, "ab") as f:              # O_APPEND 单行落盘：O(1)，与整表重写互通
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        _bump_epoch(gd)
        return row
