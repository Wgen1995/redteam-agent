# -*- coding: utf-8 -*-
"""G-5 锁探测 v2 单源（批次 6 T7；裁决 F）——state.md 会话锁四字段+OS 级探活快路。

四可选字段：lock_host/lock_pid/lock_boot/lock_since（state_md.FULL_KEY_ORDER 后缀，
v1 旧锁无四字段=解析容忍）。probe_stale 语义（保守优先）：
- 本机同 boot 且 pid 探活死 → ("dead", 理由)：manual 接管免 state-rebuild 对账前置（快路）
- 本机同 boot 且 pid 活     → ("alive", 理由)
- 跨机/跨 boot/字段缺/畸形  → ("unknown", 理由)：保守——auto 恒 REJECT、manual 维持
  对账前置+takeover-of 留痕（既有缓解不变，行为与收紧前逐字节一致）
auto 接管恒不放行（单活跃会话铁律）；本模块纯探测/纯字段产出，零账本副作用（铁律 7）。

跨平台 boot_id（R-T7-2）：Linux=/proc/sys/kernel/random/boot_id；macOS=sysctl
kern.boottime（/proc 不在，取同 boot 稳定的引导时刻串）；Windows=now-GetTickCount64
反推开机时刻（分钟取整——时钟漂移/睡眠唤醒不破同 boot 稳定）；不可得="unknown"
（probe 恒 unknown=保守路径，绝不误判 dead）。"""
import datetime
import os
import platform
import subprocess
import sys

HOST = platform.node()

_BOOT = None


def boot_id():
    """同 boot 稳定的机器纪元标识（单例缓存；不可得="unknown"=保守）。"""
    global _BOOT
    if _BOOT is None:
        _BOOT = _compute_boot_id()
    return _BOOT


def _compute_boot_id():
    try:
        if os.path.exists("/proc/sys/kernel/random/boot_id"):          # Linux
            with open("/proc/sys/kernel/random/boot_id", encoding="utf-8") as f:
                bid = f.read().strip()
                return bid or "unknown"
        if sys.platform == "darwin":                                    # macOS
            r = subprocess.run(["sysctl", "-n", "kern.boottime"],
                               capture_output=True, text=True, timeout=10)
            return "boottime=" + (r.stdout.strip() or "unknown")
        if os.name == "nt":                                             # Windows
            import ctypes
            tick_ms = ctypes.windll.kernel32.GetTickCount64()          # 开机起毫秒
            now_ms = int(datetime.datetime.now().timestamp() * 1000)
            boot_ms = now_ms - tick_ms
            minute = 60 * 1000
            boot_ms -= boot_ms % minute                                 # 分钟取整稳定
            return datetime.datetime.fromtimestamp(
                boot_ms / 1000).replace(microsecond=0).isoformat()
    except Exception:
        pass
    return "unknown"


def pid_alive(pid):
    """OS 级探活：POSIX os.kill(pid,0)（ESRCH=死/EPERM=活）；
    Windows OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION) 句柄非零=活。"""
    pid = int(pid)
    if os.name == "nt":
        import ctypes
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, pid)
        if h:
            k32.CloseHandle(h)
            return True
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True          # EPERM=进程在（属他人），按活处理（保守）
    except (OverflowError, ValueError):
        return False
    return True


def lock_fields(ts):
    """session 激活锁四字段（v2 后缀；write_cmds checkpoint --with-lock-v2 通道消费）。"""
    return {"lock_host": HOST, "lock_pid": str(os.getpid()),
            "lock_boot": boot_id(), "lock_since": ts}


def probe_stale(fields, now_host=None):
    """→ (verdict, 理由)；verdict ∈ {"dead","alive","unknown"}。
    unknown=探测不出=保守拒绝自动接管（裁决 F）；调用方语义接线在 phases_engine.run_restart。"""
    host = HOST if now_host is None else now_host
    fh, fb, fp = fields.get("lock_host"), fields.get("lock_boot"), fields.get("lock_pid")
    if not fh or not fb or fp is None or not str(fp).isdigit():
        return ("unknown", "字段缺/畸形（v1 旧锁兼容）")
    if fh != host:
        return ("unknown", "跨机（无法探测）")
    if fb != boot_id():
        return ("unknown", "跨 boot（无法探测）")
    pid = int(fp)
    if pid == os.getpid() or pid_alive(pid):
        return ("alive", "pid 探活=活")
    return ("dead", "pid 探活=死")


def _spawn_dead_pid():
    """测试锚点：已退出并收割的子进程 pid（探活必死）。惰性单例（PEP 562）——
    常规 CLI 进程零子进程代价，测试首访 DEAD_PID 才付一次。"""
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


def __getattr__(name):   # PEP 562 模块级惰性属性（DEAD_PID/BOOT 测试锚点）
    if name == "DEAD_PID":
        value = _spawn_dead_pid()
    elif name == "BOOT":
        value = boot_id()
    else:
        raise AttributeError("module %r has no attribute %r" % (__name__, name))
    globals()[name] = value
    return value
