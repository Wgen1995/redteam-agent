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
    """I-1（批次 6 评审收尾；T8 计划面）：install/hooks/<host>.md 逐宿主真挂载。

    hook_mechanism 宿主→模板 copy2 幂等覆盖至 <install_root>/hooks/<host>.md；
    模板缺=rc 1 fail-closed（「占位披露 rc 0」中间态废除——模板已交付，缺=安装树
    不完整）；无机制宿主=Tier 1+披露零落装（M-5：占位文案随之更新）。"""
    tpl = _host_template(opts["repo_root"], opts["host"])
    if not tpl.get("hook_mechanism"):
        return 0, "hooks: 宿主无 hook 机制→Tier 1+披露（落 install-log）"
    src = os.path.join(opts["repo_root"], "install", "hooks", opts["host"] + ".md")
    if not os.path.isfile(src):
        return 1, "hooks: 宿主模板缺 install/hooks/%s.md——fail-closed 拒装" % opts["host"]
    dst_dir = os.path.join(opts["install_root"], "hooks")
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(src, os.path.join(dst_dir, opts["host"] + ".md"))
    return 0, "hooks ok (%s 模板挂载→install_root/hooks)" % opts["host"]


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


CONFIRM_TOKEN = "REPLACE"   # --release 交互确认令牌（缺确认=exit 2，裁决 C）


def release_anchor(opts, confirm_stream=None):
    """I-2（批次 6 评审收尾；裁决 C 接线）：--release 信任锚替换通道。

    新锚公钥路径（--pubkey）传入 verify 面（_step1_verify_lock）替换 TEST-ONLY
    缺省锚：tools.lock 必须已在新钥下整锁重签（KEY-MANAGEMENT §5 原子变更——
    新钥与重签锁同提交落地，旧钥新锁/新钥旧锁中间态=rc 1 fail-closed）→交互
    确认（CONFIRM_TOKEN 之外输入/流关闭=rc 2 缺确认，锚文件字节零变化）→
    确认后原子替换 engines/nuclei/release.pub（tempfile 同目录+os.replace）。
    返回 (rc, msg)；release-anchor 行随 rc 落 install-log.tsv（timestamp 显式）。
    CI 与测试永续 TEST-ONLY 夹具钥（KEY-MANAGEMENT §5），本通道只在生产钥仪式
    由人工显式触发；测试经临时仓根副本驱动，绝不触真仓锚文件。"""
    repo_root = opts["repo_root"]
    pubkey = opts.get("pubkey")
    if not pubkey or not os.path.isfile(pubkey):
        rc, msg = 2, "release: 新锚公钥缺（--pubkey 路径必填）"
        _log(opts["home"], [("release-anchor", rc, msg)], opts["timestamp"])
        return rc, msg
    vcode, vmsg = _step1_verify_lock(repo_root, pubkey)
    if vcode != 0:
        rc = vcode if vcode == 1 else 2
        msg = "release: 前置校验不过（%s）——§5 原子变更：新钥与整锁重签须同提交" % vmsg
        _log(opts["home"], [("release-anchor", rc, msg.replace("\t", " "))], opts["timestamp"])
        return rc, msg
    target = os.path.join(repo_root, "engines", "nuclei", "release.pub")

    def _fp(path):
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    old_fp, new_fp = _fp(target), _fp(pubkey)
    prompt = ("[release] 信任锚替换通道（裁决 C；KEY-MANAGEMENT §4）\n"
              "[release] 目标: engines/nuclei/release.pub\n"
              "[release] 旧锚 sha256: %s\n"
              "[release] 新钥 sha256: %s\n"
              "[release] 前置校验: tools.lock 整锁新钥验签 PASS\n"
              "[release] 输入 %s 确认替换（其他输入/EOF=放弃，exit 2）: "
              % (old_fp, new_fp, CONFIRM_TOKEN))
    stream = confirm_stream if confirm_stream is not None else sys.stdin
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        line = stream.readline()
    except Exception:            # 流故障=缺确认（fail-closed 不静默）
        line = ""
    if (line or "").strip() != CONFIRM_TOKEN:
        rc, msg = 2, "release: 缺确认（输入非 %s 或流关闭）——锚文件零变化" % CONFIRM_TOKEN
        _log(opts["home"], [("release-anchor", rc, msg)], opts["timestamp"])
        return rc, msg
    # 原子替换：同目录临时文件+os.replace（换锚瞬间不留半写中间态）
    tmp = target + ".release-tmp"
    with open(pubkey, "rb") as fsrc, open(tmp, "wb") as fdst:
        fdst.write(fsrc.read())
    os.replace(tmp, target)
    rc = 0
    msg = "release: 锚已替换 old=%s new=%s（CI/测试永续 TEST-ONLY 夹具钥，§5）" % (old_fp, new_fp)
    _log(opts["home"], [("release-anchor", rc, msg)], opts["timestamp"])
    return rc, msg


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


def refresh_cve(src, knowledge_dir, ts):
    """G-32 CVE 快照显式刷新通道（裁决 D）：src=URL 或 file:// 本地路径（离线等价）。

    流程：取源→sha256 记录→临时文件经 tanyin-knowledge lint 七列校验（单源复用）→
    原子替换 cve/cve-snapshot.tsv。lint 不过=rc 1 且目标文件字节不变（先临时校验再
    原子替换）；源不可达/解码失败=rc 2/1；install-log.tsv（knowledge_dir 上级=home，
    与安装器审计通道同文件）追加 refresh-cve 行（sha256 锚定在册）。
    退出码 0=刷新成功／1=内容校验门禁失败／2=环境（源不可达）。
    非定时自动、无常驻进程：本函数只被显式人工命令（tanyin-install refresh-cve）
    调用；URL 下载=裁决 D 显式例外通道，CLI 其余命令零外联纪律不变。"""
    cve_dir = os.path.join(knowledge_dir, "cve")
    os.makedirs(cve_dir, exist_ok=True)
    target = os.path.join(cve_dir, "cve-snapshot.tsv")
    tmp = os.path.join(cve_dir, ".refresh-tmp.tsv")
    # ① 取源（file:// / 裸路径=离线等价；http(s)://=显式命令下载）
    try:
        if src.startswith("file://"):
            src_path = src[len("file://"):]
            with open(src_path, "rb") as f:
                raw = f.read()
        elif src.startswith(("http://", "https://")):
            import urllib.request  # 显式人工刷新命令专用（裁决 D）；非运行时自动外联
            with urllib.request.urlopen(src, timeout=60) as resp:
                raw = resp.read()
        else:
            with open(src, "rb") as f:
                raw = f.read()
    except OSError as e:
        _log(os.path.dirname(os.path.abspath(knowledge_dir)),
             [("refresh-cve", 2, "src 不可达=ENV %s" % src)], ts)
        return 2, "源不可达=ENV: %s" % e
    sha = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _log(os.path.dirname(os.path.abspath(knowledge_dir)),
             [("refresh-cve", 1, "非 UTF-8 内容拒绝")], ts)
        return 1, "快照非 UTF-8（fail-closed）"
    # ② 组装新文件：首行 snapshot-date=本次刷新 ts（注记纪律不变）；sha256 锚定行；
    #    源行原样转抄（源的 snapshot-date 注记行剥除—— provenance 由 sha256 行承载）
    data_lines = [ln for ln in text.splitlines()
                  if not ln.startswith("# snapshot-date")]
    nl = chr(10)
    new_text = nl.join(
        ["# snapshot-date: " + ts,
         "# source=%s sha256=%s（G-32 refresh-cve 显式命令；人工重铸等价路径见"
         " knowledge/cve/README.md）" % (src, sha)]
        + data_lines) + nl
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text)
    # ③ 七列校验复用单源：tanyin-knowledge lint（临时校验目录，不动目标）
    kn_cli = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          os.pardir, "tanyin-knowledge")
    import tempfile as _tf
    with _tf.TemporaryDirectory() as vd:
        os.makedirs(os.path.join(vd, "cve"))
        os.makedirs(os.path.join(vd, "staging"))  # lint _stage_sync 写载体目录
        with open(os.path.join(vd, "format_version"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write("kn-v1\n")
        shutil.copyfile(tmp, os.path.join(vd, "cve", "cve-snapshot.tsv"))
        r = subprocess.run([sys.executable, kn_cli, "lint",
                            "--knowledge-dir", vd, "--timestamp", ts],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300,
                           env={**os.environ, "PYTHONUTF8": "1"})
    if r.returncode != 0:
        os.remove(tmp)
        detail = (r.stdout + r.stderr).strip().splitlines()
        msg = "快照校验不过（七列 lint）: %s" % (detail[0] if detail else "rc=%d" % r.returncode)
        _log(os.path.dirname(os.path.abspath(knowledge_dir)),
             [("refresh-cve", 1, msg.replace("\t", " "))], ts)
        return 1, msg
    # ④ 原子替换+审计行（sha256 锚定在册）
    os.replace(tmp, target)
    rows = sum(1 for ln in data_lines if ln and not ln.startswith("#"))
    msg = "refresh-cve ok sha256=%s rows=%d src=%s" % (sha, rows, src)
    _log(os.path.dirname(os.path.abspath(knowledge_dir)),
         [("refresh-cve", 0, msg)], ts)
    return 0, msg


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
