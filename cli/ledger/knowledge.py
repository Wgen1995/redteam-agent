# -*- coding: utf-8 -*-
"""知识库机械运算单源（批次 5；铁律 7——语义提炼禁入，本模块只做：
schema 校验/脱敏哨兵/去重哈希/确定性导出/三元组匹配/基线查表/CPE 离线匹配）。

载体（R7）：仓库 knowledge/=种子库（format_version=kn-v1；批次 6 安装器拷贝至
$TANYIN_HOME/knowledge/）；CLI 一律 --knowledge-dir 参数化；种子库只读纪律——
指向仓库 knowledge/ 时一切写子命令（source-register/approve/commit/promote/demote/
client-map add）REJECT（exit 1，防 CI 误写种子）。退出码对齐 Strix：
0=通过 / 1=门禁失败（Reject） / 2=用法或环境问题（KnowledgeError）。"""
import hashlib
import os

FORMAT_VERSION = "kn-v1"
DIRS = ("concepts", "precedents", "entities", "targets", "patterns/core",
        "patterns/learned", "business", "retros", "methodology", "cve",
        "sources", "staging/pages", "checklists")
FILES = {"format_version": FORMAT_VERSION + "\n"}

# R7 种子库只读纪律：写子命令守卫集（client-map 按 add 动词判——next/list 只读）
WRITE_SUBS = ("source-register", "approve", "commit", "promote", "demote")


class KnowledgeError(Exception):
    """exit 2：结构/版本/环境问题。"""


class Reject(Exception):
    """exit 1：门禁失败（种子库只读/校验不过/状态机非法迁移）。"""


def repo_seed_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge"))


def load_ctx(kdir):
    """版本门：format_version 不匹配=拒绝操作并提示迁移（契约 14 §1）。"""
    if not os.path.isdir(kdir):
        raise KnowledgeError("knowledge 目录不存在: " + kdir)
    fv = os.path.join(kdir, "format_version")
    if not os.path.isfile(fv) or open(fv, encoding="utf-8").read().strip() != FORMAT_VERSION:
        raise KnowledgeError("format_version 不匹配（期望 %s）——拒绝操作，先跑迁移/重铸" % FORMAT_VERSION)
    return kdir


def guard_writable(kdir, sub, rest):
    """R7：种子库只读——写子命令指向仓库 knowledge/ 时 REJECT（exit 1）。"""
    guarded = sub in WRITE_SUBS or (sub == "client-map" and "add" in rest)
    if not guarded:
        return
    seed = repo_seed_root()
    if os.path.abspath(kdir) == seed:
        raise Reject("种子库只读（仓库 knowledge/ = 发行内容；写操作请在运行时库执行）: " + kdir)


def init(kdir):
    """骨架初始化（幂等：已初始化=PASS no-op）。"""
    os.makedirs(kdir, exist_ok=True)
    for sub in DIRS:
        os.makedirs(os.path.join(kdir, sub), exist_ok=True)
    for name, content in FILES.items():
        p = os.path.join(kdir, name)
        if not os.path.isfile(p):
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
    for name in ("index.md", "log.md", "overview.md"):
        p = os.path.join(kdir, name)
        if not os.path.isfile(p):
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write("# %s\n\n（init 生成；commit 时重生成 index/overview）\n" % name[:-3])
    return 0
