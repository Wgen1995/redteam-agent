# -*- coding: utf-8 -*-
"""tanyin-selfcheck 六项静态检查单源（批次 6 T6；铁律 7「安装自检」能力面）。

六项：cmd-index / encoding / phases-schema / layout / lock-verify / golden。
- run_static(install_root, home, repo_root) -> (worst_rc, [(检查名, rc, 明细)])；
  install_root/home=None 时用仓内默认展开（仓内自检形态）。
- run_guided(host) -> 一页手测引导（安装命令→能力探测→冒烟清单→回传模板；
  宿主模板缺=SystemExit(2) 用法错误）。
- 退出码沿 0/1/2：门禁不过=1（含六项任一）；openssl/公钥缺=ENV=2。
- encoding 扫描范围=REPO_FILES_SCAN 五目录（安装随行资产；panorama/tests/docs/git
  不进任何检查命令——与 install_core._AUTH 白名单同源纪律）。"""
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ledger import supply_chain  # noqa: E402
from ledger.install_core import DEFAULT_HOME_expanded, DEFAULT_INSTALL_ROOT_expanded  # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ENV = {**os.environ, "PYTHONUTF8": "1"}
REPO_FILES_SCAN = ("phases", "engines", "cli", "shared", "install")
_TEXT_EXTS = {".md", ".py", ".json", ".tsv", ".yaml", ".lock"}

# KNOWN_COMMANDS：已知命令面冻结清单（2026-09-24 执行期枚举固化；ledger=registry
# 单源 all_commands()+ledger- 前缀孪生，其余=各工具用法面实测）。
# 新增命令忘记登记=cmd-index 红（与 VulnClaw verify_execution_boundary 同型机械防线）；
# 交付新命令/新工具的任务须随行更新本表（forward 面——如 tanyin-report/egress serve——
# 随其交付任务入表，此前文档若出现带子命令的引用即红=有意绊线）。
KNOWN_COMMANDS = {
    "ledger": ["add-asset", "add-cred", "add-edge", "add-evidence", "add-fact",
               "add-finding", "add-goal", "add-intent", "add-scope", "amend-scope",
               "append-timeline", "approve", "budget-check", "budget-log", "checkpoint",
               "cleanup-checklist", "converge-check", "graph-horizon", "graph-neighbors",
               "graph-paths", "hash-recheck", "intent-status", "ledger-add-asset",
               "ledger-add-cred", "ledger-add-edge", "ledger-add-evidence",
               "ledger-add-fact", "ledger-add-finding", "ledger-add-goal",
               "ledger-add-intent", "ledger-add-scope", "ledger-amend-scope",
               "ledger-append-timeline", "ledger-approve", "ledger-budget-log",
               "ledger-checkpoint", "ledger-matrix-freeze", "ledger-matrix-set",
               "ledger-replay-summary", "ledger-scope-coverage", "ledger-set-cred-status",
               "ledger-set-intent-status", "ledger-supersede-finding",
               "ledger-terminal-gate", "ledger-tree-check", "matrix-audit",
               "matrix-freeze", "matrix-gaps", "matrix-get", "matrix-init", "matrix-set",
               "next-id", "pending-intents", "redact-scan", "scope-check",
               "set-cred-status", "set-intent-status", "set-replay-state",
               "state-rebuild", "supersede-finding", "unconsumed-facts", "validate",
               "verify-chain"],
    "phases": ["cached", "denominator-ready", "gate", "rebuild-state", "restart",
               "resume-kit", "trigger-audit", "validate"],
    "guard": ["deploy-vault", "exec", "inject"],
    "egress": ["compile", "dry-run", "verify"],
    "canary": ["deploy", "probe", "recon-deploy", "recon-recall"],
    "knowledge": ["approve", "client-map", "commit", "demote", "export", "init",
                  "lint", "match", "neighbors", "nday-match", "promote", "score",
                  "source-register"],
    "redact": [],
    "replay": ["matcher-test", "replay"],
    "viz": ["render"],
    "budgetctl": ["enforce", "rate"],
    "evals": ["list", "report", "run"],
    "install": ["refresh-cve"],  # 批次 6 T9：G-32 显式刷新通道（新面随行入表）
}

# 引用形态：tanyin-<tool> <sub>（子命令 token 限 ASCII 小写字母/数字/连字符——
# 中英文混排散文「tanyin-ledger 的 add-goal」自然不组成配对）
_REF = re.compile(r"tanyin-([a-z][a-z0-9-]*)[ \t]+([a-z][a-z0-9-]*)")


def check_cmd_index(repo_root):
    """①phases/*.md+engines/**/MANIFEST.md 中 tanyin-<tool> <sub> 引用 ⊆ 已知命令面。"""
    targets = []
    ph = os.path.join(repo_root, "phases")
    if os.path.isdir(ph):
        targets += [os.path.join(ph, f) for f in sorted(os.listdir(ph)) if f.endswith(".md")]
    eng = os.path.join(repo_root, "engines")
    if os.path.isdir(eng):
        for root, dirs, files in os.walk(eng):
            for f in files:
                if f == "MANIFEST.md":
                    targets.append(os.path.join(root, f))
    for p in targets:
        with open(p, encoding="utf-8") as f:
            for i, ln in enumerate(f, 1):
                for tool, sub in _REF.findall(ln):
                    known = KNOWN_COMMANDS.get(tool)
                    if known is None:
                        return 1
                    if sub not in known:
                        return 1
    return 0


def check_encoding(root):
    """②UTF-8 无 BOM+无 CRLF（*.md/*.py/*.json/*.tsv/*.yaml/*.lock）。"""
    for r, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in (".git", "__pycache__")]
        for fn in files:
            if os.path.splitext(fn)[1] not in _TEXT_EXTS:
                continue
            p = os.path.join(r, fn)
            with open(p, "rb") as f:
                b = f.read()
            if b.startswith(b"\xef\xbb\xbf"):
                return 1
            if b"\r\n" in b:
                return 1
            try:
                b.decode("utf-8")
            except UnicodeDecodeError:
                return 1
    return 0


def check_phases_schema(repo_root):
    """③tanyin-phases validate（phases.yaml 契约面）。"""
    r = subprocess.run([sys.executable, os.path.join(repo_root, "cli", "tanyin-phases"),
                        "validate"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300, cwd=repo_root, env=_ENV)
    return r.returncode


def check_layout(install_root, home):
    """④安装区/交战区分离（§3.4）：home 不得在 install_root 内。"""
    ir, hm = os.path.abspath(install_root), os.path.abspath(home)
    if hm == ir or hm.startswith(ir + os.sep):
        return 1
    return 0


def check_lock(repo_root, pubkey=None):
    """⑤supply_chain.load_lock+verify_entry 全键；openssl/公钥缺=2（ENV）。"""
    lock = os.path.join(repo_root, "tools.lock")
    if not os.path.exists(lock):
        return 1
    if shutil.which("openssl") is None:
        return 2
    pub = pubkey or os.path.join(repo_root, "engines", "nuclei", "release.pub")
    if not os.path.exists(pub):
        return 2
    for e in supply_chain.load_lock(lock).values():
        ok, _ = supply_chain.verify_entry(e, pub)
        if not ok:
            return 1
    return 0


def check_golden(repo_root):
    """⑥金样回归（tests/run_golden.py 脚本子进程实跑——防空绿假 PASS 先例 R-T1-1）。"""
    r = subprocess.run([sys.executable, os.path.join(repo_root, "tests", "run_golden.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=1800, cwd=repo_root, env=_ENV)
    return r.returncode


def run_static(install_root, home, repo_root):
    """六项静态检查；返回 (worst_rc, [(检查名, rc, 明细)])。"""
    ir = install_root or DEFAULT_INSTALL_ROOT_expanded()
    hm = home or DEFAULT_HOME_expanded()
    enc = max((check_encoding(os.path.join(repo_root, d))
               for d in REPO_FILES_SCAN if os.path.isdir(os.path.join(repo_root, d))),
              default=0)
    items = [
        ("cmd-index", check_cmd_index(repo_root),
         "phases/*.md+engines/**/MANIFEST.md 引用 ⊆ KNOWN_COMMANDS"),
        ("encoding", enc, "UTF-8 无 BOM+LF（%s）" % "/".join(REPO_FILES_SCAN)),
        ("phases-schema", check_phases_schema(repo_root), "tanyin-phases validate"),
        ("layout", check_layout(ir, hm), "交战区分离 §3.4（home ∉ install_root）"),
        ("lock-verify", check_lock(repo_root), "tools.lock 验签（supply_chain 单源）"),
        ("golden", check_golden(repo_root), "tests/run_golden.py"),
    ]
    worst = max((c for _, c, _ in items), default=0)
    return worst, items


GUIDED_TMPL = """# {host} 手测引导（§10.3；发布口径={verification}）
1 安装命令：py -3 cli/tanyin-install --host {host} --timestamp <TS>
2 能力探测（逐项自动+人工确认）：子代理并发/shell/headless/系统级注入/hook 挂载点
3 冒烟清单：「用探隐自检」干跑 P0-P2——零对外请求，产出 goals/scope/matrix 样本+timeline
4 回传模板（贴回 issue 即计入验证记录）：
{{"host":"{host}","probe_results":{{...}},"dryrun_artifacts_sha256":"...","anomalies":"..."}}
5 发布口径：{verification}；执法档位默认 Tier {tier}（保守披露）
6 未实测披露：静态验证/CI 不替代宿主手测——探测项完成前保持「未实测」标注
"""


def run_guided(host):
    path = os.path.join(_REPO, "install", "hosts", host + ".json")
    if not os.path.exists(path):
        raise SystemExit(2)   # 未知宿主=用法错误 exit 2
    with open(path, encoding="utf-8") as f:
        tpl = json.load(f)
    return GUIDED_TMPL.format(host=host,
                              verification=tpl.get("verification", ""),
                              tier=tpl.get("egress_default_tier", 1))
