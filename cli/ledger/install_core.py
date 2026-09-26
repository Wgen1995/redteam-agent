# -*- coding: utf-8 -*-
"""tanyin-install 六步安装单源（批次 6 T5；铁律 7「安装自检」能力面）。

六步：verify-lock → authoritative-dir → host-link → hooks → init-home → selfcheck。
- 退出码沿契约 09 面：0=通过／1=门禁失败（lock 验签不过、链接冲突）／2=环境问题
  （openssl/pubkey 缺、symlink 权限）。
- 幂等（设计 §10.1）：copytree dirs_exist_ok=True+重链不报错；snapshot() 对树内容
  做哈希投影供二次安装零变更断言（install-log.tsv=追加式审计通道，不入投影——
  审计行本身记录"本次零变更"，逐次追加是日志的本职）。
- 交战区分离（设计 §3.4）：home（engagements/knowledge/report）永不落安装树内；
  step2 白名单拷贝（_AUTH），panorama/tests/docs/git 天然不进任何安装命令。
- R-T12-4：step5 拷贝 knowledge 种树（含 methodology/k1-baseline.tsv）到运行时库。
- 时间戳一律调用方显式传入（禁墙钟进安装日志，evals 可重放纪律同源）。"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ledger import supply_chain  # noqa: E402

DEFAULT_INSTALL_ROOT = os.path.join("~", ".local", "share", "tanyin")
DEFAULT_HOME = os.path.join("~", ".tanyin")
STEPS = ("verify-lock", "authoritative-dir", "host-link", "hooks", "init-home", "selfcheck")
# 权威目录白名单：装到 install_root 的仓内容（.git/tests/docs/panorama 不在名单=不进安装树）
_AUTH = ("SKILL.md", "phases", "engines", "cli", "shared", "install", "contracts", "tools.lock")
_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".git")
_LOG_NAME = "install-log.tsv"


def DEFAULT_INSTALL_ROOT_expanded():
    return os.path.abspath(os.path.expanduser(DEFAULT_INSTALL_ROOT))


def DEFAULT_HOME_expanded():
    return os.path.abspath(os.path.expanduser(DEFAULT_HOME))


def _host_template(repo_root, host):
    path = os.path.join(repo_root, "install", "hosts", host + ".json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _step1_verify_lock(repo_root, pubkey):
    lock = os.path.join(repo_root, "tools.lock")
    if not os.path.exists(lock):
        # 锁文件缺=无法验签=fail-closed 门禁失败（非环境问题，不静默放行）
        return 1, "tools.lock 缺（供应链锁不可验）"
    if shutil.which("openssl") is None:
        return 2, "openssl 缺席=ENV（验签 fail-closed）"
    if not pubkey or not os.path.exists(pubkey):
        return 2, "信任锚公钥缺=ENV: %s" % (pubkey or "<default>")
    entries = supply_chain.load_lock(lock)
    for e in entries.values():
        # verify_entry 形参=公钥路径（透传 openssl -inkey），非公钥字节（计划草图笔误：
        # 读字节作路径传参恒验签失败——R-T5-1 按批次 4 单源实签名修正）
        ok, reason = supply_chain.verify_entry(e, pubkey)
        if not ok:
            return 1, "tools.lock 验签失败: %s (%s)" % (e.get("key"), reason)
    return 0, "verify-lock ok (%d 键)" % len(entries)


def _step2_authoritative(opts):
    n = 0
    for name in _AUTH:
        src = os.path.join(opts["repo_root"], name)
        dst = os.path.join(opts["install_root"], name)
        if not os.path.exists(src):
            return 1, "权威项缺（安装树不完整）: %s" % name
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True, ignore=_IGNORE)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        n += 1
    return 0, "authoritative-dir ok (%d 项)" % n


def _skill_target(opts, rel):
    return os.path.join(opts["home"], "hosts", opts["host"], rel, "tanyin")


def _step3_host_link(opts):
    tpl = _host_template(opts["repo_root"], opts["host"])
    links = 0
    for rel in tpl.get("skill_link_dirs", []):
        target = _skill_target(opts, rel)
        src = os.path.abspath(opts["install_root"])
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if os.path.islink(target):
            os.remove(target)                       # 幂等：重链不报错
        elif os.path.exists(target):
            return 1, "host-link 冲突: %s 非链接（用户文件零触碰）" % target
        try:
            os.symlink(src, target)
        except (OSError, NotImplementedError) as e:
            return 2, "symlink 创建失败=ENV（Windows 需开发者模式）: %s" % e
        links += 1
    return 0, "host-link ok (%d 链接)" % links


def _step4_hooks(opts):
    tpl = _host_template(opts["repo_root"], opts["host"])
    if not tpl.get("hook_mechanism"):
        return 0, "hooks: 宿主无 hook 机制→Tier 1+披露（落 install-log）"
    src = os.path.join(opts["repo_root"], "install", "hooks")
    if not os.path.isdir(src):
        # 模板目录批次 6 T8 落地；落盘前占位披露（不阻塞安装）
        return 0, "hooks: 模板未在库（批次6 T8 落地前占位披露）"
    dst = os.path.join(opts["install_root"], "hooks", opts["host"])
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=_IGNORE)
    return 0, "hooks ok (%s)" % opts["host"]


def _step5_init_home(opts):
    for sub in ("engagements", "knowledge", "report"):
        os.makedirs(os.path.join(opts["home"], sub), exist_ok=True)
    seed = os.path.join(opts["repo_root"], "knowledge")
    if os.path.isdir(seed):
        # R-T12-4：k1-baseline 等方法库随种树进运行时库（交战区侧，与安装区分离）
        shutil.copytree(seed, os.path.join(opts["home"], "knowledge"),
                        dirs_exist_ok=True, ignore=_IGNORE)
    open(os.path.join(opts["home"], ".gitignore"), "a", encoding="utf-8").close()
    return 0, "init-home ok（engagements/knowledge 与安装区分离）"


def _step6_selfcheck_gate(opts):
    sc = os.path.join(opts["repo_root"], "cli", "tanyin-selfcheck")
    if not os.path.exists(sc):
        # 入口缺=安装树不完整（ENV；非 T5 的 pending 中间态——该分支 T6 已删）
        return 2, "selfcheck 入口缺（ENV/安装树不完整）"
    r = subprocess.run([sys.executable, sc, "--static",
                        "--install-root", opts["install_root"],
                        "--home", opts["home"]],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=1800,
                       cwd=opts["repo_root"], env={**os.environ, "PYTHONUTF8": "1"})
    return (0 if r.returncode == 0 else r.returncode), "selfcheck rc=%d" % r.returncode


def install(opts):
    """六步安装；返回 (worst_rc, 摘要)。opts 键：install_root/home/host/repo_root/
    pubkey/timestamp（timestamp 必填——禁墙钟进安装日志）。"""
    if not opts.get("timestamp"):
        raise ValueError("timestamp 必填（显式 ISO8601；禁墙钟进账纪律）")
    pubkey = opts.get("pubkey") or os.path.join(opts["repo_root"], "engines",
                                                "nuclei", "release.pub")
    results = [("verify-lock",) + _step1_verify_lock(opts["repo_root"], pubkey)]
    if results[0][1] == 0:
        for step, fn in ((STEPS[1], _step2_authoritative), (STEPS[2], _step3_host_link),
                         (STEPS[3], _step4_hooks), (STEPS[4], _step5_init_home),
                         (STEPS[5], _step6_selfcheck_gate)):
            c, m = fn(opts)
            results.append((step, c, m))
    _log(opts["home"], results, opts["timestamp"])
    has_gate_fail = any(c == 1 for _, c, _ in results)
    has_env = any(c == 2 for _, c, _ in results)
    worst = 1 if has_gate_fail else (2 if has_env else 0)
    return worst, "; ".join("%s=%d" % (s, c) for s, c, _ in results)


def _log(home, results, ts):
    os.makedirs(home, exist_ok=True)
    with open(os.path.join(home, _LOG_NAME), "a", encoding="utf-8", newline="\n") as f:
        for step, c, m in results:
            f.write("%s\t%s\trc=%d %s\n" % (ts, step, c, str(m).replace("\t", " ")))


def snapshot(install_root, home):
    """树内容哈希投影（幂等断言面）；install-log.tsv 除外（追加式审计通道）。"""
    out = []
    for base in (install_root, home):
        for root, dirs, files in os.walk(base):
            dirs[:] = [x for x in dirs if x not in (".git", "__pycache__")]
            for fn in sorted(files):
                if fn == _LOG_NAME:
                    continue
                p = os.path.join(root, fn)
                with open(p, "rb") as f:
                    out.append((os.path.relpath(p, base),
                                hashlib.sha256(f.read()).hexdigest()))
    return sorted(out)


def link_report(opts):
    """宿主链接体检：[(target, ok)]；ok=是链接且目标可达（安装树在位）。"""
    tpl = _host_template(opts["repo_root"], opts["host"])
    links = []
    for rel in tpl.get("skill_link_dirs", []):
        target = _skill_target(opts, rel)
        links.append((target, os.path.islink(target) and os.path.exists(target)))
    return {"links": links}
