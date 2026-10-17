# -*- coding: utf-8 -*-
"""W2·01P0-4 · 多战执法面——并发战资源仲裁核（注册表式）。

来源：docs/reviews/2026-10-17-exceed-review/01-架构专家.md P0-4「战斗注册表
（battle home 侧 registry，状态机 running/…+并发上限）；全局并发闸+每战资源帽
（LLM 配额/出网带宽共享仲裁）」。本模块=注册表与仲裁的确定性核：

- 注册表：battles 根下 registry.json（schema_version 锚；temp+rename 原子写；
  环境锁 fcntl.flock 防并发 admit 撕裂——多战执法面不允许检查-写入竞态）。
- 预算仲裁：在册活战 budget_usd 合计+新战申报 ≤ cap_budget_usd（None=不设帽，
  登记仍在）；拒绝判决带数学披露（used+new>cap 原数入档）。
- 端口冲突检测：活战占用端口集互斥；forbid_ports=平台保留端口（8900/3000/
  8787/8443 类——操作员面常驻服务禁夺）。claim_ports 供 runner 起代理后补占。
- 死 pid 回收：admit 仲裁前先收尸（pid 不活的在册行=战已终，预算/端口全释放，
  条目出册）——注册表不靠人工清册，重启后自愈。
- 纪律：损坏 registry.json=fail-closed ValueError（零执法静默降级）；
  Python 3.9 纯 stdlib；本模块是运行态执法面（非账本），wall 钟仅入
  registered_at 留痕，判决逻辑零取钟（now/pid_alive 全可注入=确定性可测）。
"""
import errno
import json
import os
import re
import tempfile
import time

REGISTRY_NAME = "registry.json"
REGISTRY_SCHEMA = 1
_BATTLE = re.compile(r"^battle-(\d+)$")
_EPS = 1e-9
_PIDLESS_GRACE_S = 300.0   # 无 pid 条目（admit→spawn→set_pid 窗口）宽限回收


def _default_pid_alive(pid):
    """OS 事实：pid 活性（os.kill 0 探测；权限/不存在=死）。"""
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _reg_path(root):
    return os.path.join(root, REGISTRY_NAME)


def _load(root):
    """读注册表；缺件=空册；损坏=fail-closed（ValueError，不静默重置）。"""
    p = _reg_path(root)
    if not os.path.isfile(p):
        return {"schema_version": REGISTRY_SCHEMA, "entries": {}}
    try:
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError) as e:
        raise ValueError("registry.json 损坏（fail-closed，先人工处置再点火）: %s" % e)
    if not isinstance(doc, dict) or not isinstance(doc.get("entries"), dict) \
            or doc.get("schema_version") != REGISTRY_SCHEMA:
        raise ValueError("registry.json 结构不合法（schema_version=%s）"
                         % doc.get("schema_version"))
    return doc


def _save(root, doc):
    """原子写（temp+rename；同目录保 rename 原子性）。"""
    os.makedirs(root, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=root, prefix=".registry.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, _reg_path(root))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _lock(root):
    """环境锁（fcntl.flock 独占）——admit/release/claim 的检查-写入全 enclosed。"""
    import contextlib

    @contextlib.contextmanager
    def cm():
        os.makedirs(root, exist_ok=True)
        lock_path = _reg_path(root) + ".lock"
        f = open(lock_path, "a+", encoding="utf-8")
        try:
            try:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            except (ImportError, OSError):
                pass          # 非 POSIX 无 flock=单进程串行兜底（写入仍原子）
            yield
        finally:
            f.close()
    return cm()


def _reap(doc, pid_alive, now):
    """死 pid 在册行出册（含过宽限的无 pid 行）；返回被回收战名。"""
    dead = []
    for battle, e in list(doc["entries"].items()):
        if pid_alive(e.get("pid")):
            continue
        if e.get("pid") is None and (now - float(e.get("registered_at") or 0)) < _PIDLESS_GRACE_S:
            continue
        dead.append(battle)
        del doc["entries"][battle]
    return dead


def admit(root, battle, *, budget_usd=0.0, ports=(), pid=None,
          cap_budget_usd=None, forbid_ports=(), pid_alive=None, now=None):
    """并发战资源仲裁+登记。允许=登记入册并持久化；拒绝=零变更零入册。

    返回判决 {allowed, reason?, battle, budget_used, budget_cap?, conflict_ports?,
    reaped?}；reason ∈ {already-registered, budget-cap, port-conflict,
    port-forbidden}。battle 须 battle-N 形（ValueError=调用方程序错）。
    """
    if not _BATTLE.match(battle or ""):
        raise ValueError("battle 须 battle-N 形: %r" % (battle,))
    pid_alive = pid_alive or _default_pid_alive
    now = time.time() if now is None else now
    with _lock(root):
        doc = _load(root)
        reaped = _reap(doc, pid_alive, now)
        if battle in doc["entries"]:
            return {"allowed": False, "reason": "already-registered",
                    "battle": battle, "budget_used": _used(doc),
                    "conflict_ports": [], "reaped": reaped}
        used = _used(doc)
        if cap_budget_usd is not None and used + float(budget_usd) > float(cap_budget_usd) + _EPS:
            return {"allowed": False, "reason": "budget-cap", "battle": battle,
                    "budget_used": used, "budget_cap": float(cap_budget_usd),
                    "budget_demand": used + float(budget_usd),   # 数学披露
                    "conflict_ports": [], "reaped": reaped}
        held = _held_ports(doc)
        conflict = sorted(set(int(p) for p in ports) & held)
        if conflict:
            return {"allowed": False, "reason": "port-conflict", "battle": battle,
                    "budget_used": used, "conflict_ports": conflict, "reaped": reaped}
        forbid = sorted(set(int(p) for p in ports) & set(int(p) for p in forbid_ports))
        if forbid:
            return {"allowed": False, "reason": "port-forbidden", "battle": battle,
                    "budget_used": used, "conflict_ports": forbid, "reaped": reaped}
        doc["entries"][battle] = {"battle": battle, "pid": pid,
                                  "budget_usd": float(budget_usd),
                                  "ports": sorted(set(int(p) for p in ports)),
                                  "registered_at": now}
        _save(root, doc)
        return {"allowed": True, "battle": battle,
                "budget_used": used + float(budget_usd), "reaped": reaped}


def release(root, battle):
    """出册（战毕/停战）：释放预算与端口。返回 freed 摘要；不在册=None。"""
    with _lock(root):
        doc = _load(root)
        e = doc["entries"].pop(battle, None)
        if e is None:
            return None
        _save(root, doc)
        return {"battle": battle, "freed_budget_usd": e.get("budget_usd", 0.0),
                "freed_ports": list(e.get("ports", []))}


def set_pid(root, battle, pid):
    """补记 pid（admit→spawn→set_pid 点火窗口）；不在册=None。"""
    with _lock(root):
        doc = _load(root)
        e = doc["entries"].get(battle)
        if e is None:
            return None
        e["pid"] = pid
        _save(root, doc)
        return {"battle": battle, "pid": pid}


def claim_ports(root, battle, ports, *, forbid_ports=(), pid_alive=None, now=None):
    """活战补占端口（runner 起 egress 代理后回填）；冲突/保留=拒绝零变更。"""
    pid_alive = pid_alive or _default_pid_alive
    now = time.time() if now is None else now
    with _lock(root):
        doc = _load(root)
        _reap(doc, pid_alive, now)
        e = doc["entries"].get(battle)
        if e is None:
            return {"allowed": False, "reason": "not-registered", "battle": battle,
                    "conflict_ports": []}
        held = _held_ports(doc) - set(int(p) for p in e.get("ports", []))
        conflict = sorted(set(int(p) for p in ports) & held)
        forbid = sorted(set(int(p) for p in ports) & set(int(p) for p in forbid_ports))
        if conflict or forbid:
            return {"allowed": False,
                    "reason": "port-conflict" if conflict else "port-forbidden",
                    "battle": battle,
                    "conflict_ports": conflict or forbid}
        e["ports"] = sorted(set(int(p) for p in e.get("ports", []))
                            | set(int(p) for p in ports))
        _save(root, doc)
        return {"allowed": True, "battle": battle, "ports": list(e["ports"])}


def snapshot(root):
    """只读盘点（仪表盘/队列视图数据面）：不回收不改册。"""
    doc = _load(root)
    entries = [dict(doc["entries"][b], battle=b)
               for b in sorted(doc["entries"])]
    return {"schema_version": doc["schema_version"], "entries": entries,
            "budget_used": _used(doc)}


def _used(doc):
    return sum(float(e.get("budget_usd") or 0.0) for e in doc["entries"].values())


def _held_ports(doc):
    out = set()
    for e in doc["entries"].values():
        out |= set(int(p) for p in e.get("ports", []))
    return out
