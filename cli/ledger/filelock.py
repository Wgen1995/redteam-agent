# -*- coding: utf-8 -*-
"""goal 级写锁（批次 7 T2，C1 并发半边）——跨平台文件锁单源。
锁文件 <goal-dir>/.lock 不进 13 表（core.TABLES 之外：金样/fingerprint/链哈希零干扰）。
POSIX=flock LOCK_EX 阻塞；Windows=msvcrt LK_NBLCK 自旋+超时。超时=OSError，由调用方
按退出码契约翻译为 2（环境/资源类）。
死锁论证：锁取自 registry.lookup 分发单点（写命令处理注册表派生面），且写命令处理函数
自身不再经 registry.lookup 嵌套调用其他写命令（grep 复核 write_cmds/matrix_init 零
lookup 调用）——同进程恒为顺序取/放，无 flock 自锁；phases_engine 对 budget-log/
append-timeline/checkpoint 的内部组合调用各为独立取放区间，顺序无嵌套。"""
import contextlib, os, time


def _lock_nt(fd, timeout):
    import msvcrt
    deadline = time.monotonic() + timeout
    while True:
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.05)


def _unlock_nt(fd):
    import msvcrt
    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)


@contextlib.contextmanager
def goal_lock(goal_dir, timeout=30.0):
    # exist_ok：add-goal 类新目场景锁先于首写存在（无目录则无账本可护，建目录=与
    # 写路径 commit 侧 makedirs 同语义，不新增表面行为）
    os.makedirs(goal_dir, exist_ok=True)
    p = os.path.join(goal_dir, ".lock")
    fd = os.open(p, os.O_CREAT | os.O_RDWR)
    try:
        if os.name == "nt":
            _lock_nt(fd, timeout)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            if os.name == "nt":
                _unlock_nt(fd)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(fd)
