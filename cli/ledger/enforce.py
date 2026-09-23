# -*- coding: utf-8 -*-
"""enforce —— Tier 1（tanyin-guard）与 Tier 2（hooks/simulate.py）同源执法逻辑。

SECW-3：hooks 三模板声明「deny-list 比对 + scope 解析」同源语义，此前 simulate.py
只实现 deny-list 半边（SECW-1 盘点差距 1）。抽出单源防两份漂移：
deny-list / scope include/exclude/oob 加载 / 主机提取 / 界外判定。scope.tsv 缺失=include
为空=一切带主机命令界外（fail-closed，契约 11 Tier 2 行）。

批次 2 审计洞 1 修复（exclude 语义缺失）：load_scope 返回 include/exclude/oob 三集
（amendment 链后行覆盖先行，契约 05 §3）；判定顺序=先 include 命中，再 exclude 命中
即拒（exclude 优先于 include）；oob=契约 05「界外=记不测」——Tier1/Tier2 对 oob 主机
不做主动测试（REJECT 注明 oob），仅 Tier3 egress 放行其回连。tanyin-egress compile
同用 load_scope——账本=执法策略单一事实源，消除两层解释矛盾。
"""
import ipaddress
import os
import re

from .schemas import TABLES

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DENYLIST_PATH = os.path.join(_REPO_ROOT, "shared", "DENYLIST.md")

# 主机形态判据（提取强化，审计 Important #6）：
# - 域名：≥2 个点分标签，标签 [a-z0-9-] 且首尾非连字符，至少一个标签含字母
#   （排除 "3.14"/"1.2.3" 等纯数字版本号形态）；
# - IPv4：恰 4 个纯数字标签；IPv6：仅 hex+冒号且 ≥2 个冒号（::1/2001:db8::1）；
# - localhost 单列（无点，环回别名）。
# 提取位：token 整体 + key=value 的值段（--target=evil.com / url=https://e.com/x），
# 依次剥 scheme://、userinfo@、路径/?#、[v6]:port 括号与 :port。
_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", re.IGNORECASE)
_IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
_IPV6_RE = re.compile(r"^[0-9a-fA-F:]+$")


# 内嵌兜底=shared/DENYLIST.md 同份拷贝（缺文件/不可读/空清单时启用；两处必须
# 同步改——tests/test_enforce_unit.py::DenyListData 钉死一致）。
# 「format 」含尾随空格：命中 "format c:" 而不误伤 information。
DENY_EMBEDDED = [
    "rm -rf /", "rm -rf ./", "rm -rf .", "rm -fr /", "rm -fr ./", "rm -fr .",
    "rm -rf ~", "rm -fr ~",
    "drop database", "truncate table",
    ":(){:|:&};:", ":(){ :|:& };:",
    "mkfs", "dd if=", "dd of=/dev/",
    "shutdown", "reboot", "halt", "init 0", "init 6",
    "format ", "> /dev/sd", "> /dev/vd", "chmod -R 777 /",
]


def parse_denylist(text):
    """DENYLIST.md 解析：'- ' 列表项为模式（保留模式内/尾随空格，仅视为行数据）。"""
    pats = []
    for line in text.splitlines():
        if line.startswith("- "):
            p = line[2:].rstrip(chr(13))
            if p:
                pats.append(p)
    return pats


def load_denylist(root=None):
    """deny-list 数据化（审计 Important #5，设计 §8.3）：shared/DENYLIST.md 为源，
    缺文件/不可读/空清单时回落内嵌同份兜底（fail-closed）。"""
    p = os.path.join(root, "shared", "DENYLIST.md") if root else DENYLIST_PATH
    try:
        with open(p, encoding="utf-8") as f:
            pats = parse_denylist(f.read())
    except OSError:
        pats = []
    return pats or list(DENY_EMBEDDED)


DENY_LIST = load_denylist()


def deny_hit(joined):
    for d in DENY_LIST:
        if d in joined:
            return d
    return None


def load_scope(session):
    """scope.tsv 生效链解析（执法策略单一事实源，Tier1/Tier2/Tier3 共用）。

    amendment 语义（契约 05 §3）：同 matcher 后行覆盖先行。返回
    {"include": [...], "exclude": [...], "oob": [...]}；account-grant 行不参与
    主机判定。scope.tsv 缺失=三集皆空=一切带主机命令界外（fail-closed）。
    """
    sf = TABLES["scope.tsv"]
    ki, mi = sf.index("kind"), sf.index("matcher")
    eff, order = {}, []
    for r in session.rows("scope.tsv"):
        m = r[mi]
        if m not in eff:
            order.append(m)
        eff[m] = r[ki]
    out = {"include": [], "exclude": [], "oob": []}
    for m in order:
        if eff[m] in out:
            out[eff[m]].append(m)
    return out


def host_in_scope(host, matchers):
    if not host:
        return True
    h = host.lower().rstrip(".")
    for m in matchers:
        m = m.lower()
        if m.startswith("*."):
            if h == m[2:] or h.endswith("." + m[2:]):
                return True
        elif "/" in m:
            try:
                if ipaddress.ip_address(h) in ipaddress.ip_network(m, strict=False):
                    return True
            except (ValueError, TypeError):
                pass  # TypeError=IPv6 主机对 IPv4 网段（版本不匹配），非命中
        elif h == m or h.endswith("." + m):
            return True
    return False


def scope_verdict(host, scope):
    """单主机判定（契约 05 kind 三值语义）：

    - exclude 命中 -> "exclude"（排除项，优先于 include：include 内的被排除主机即拒）
    - include 命中 -> "in"
    - 仅 oob 命中   -> "oob"（界外=记不测：Tier1/Tier2 不做主动测试，仅 Tier3 回连白名单）
    - 都未命中      -> "out"（界外）
    """
    if not host:
        return "in"
    if host_in_scope(host, scope["exclude"]):
        return "exclude"
    if host_in_scope(host, scope["include"]):
        return "in"
    if host_in_scope(host, scope["oob"]):
        return "oob"
    return "out"


def out_of_scope_hosts(args, scope):
    """按出现序返回界外主机及判定（去重保序）：[(host, verdict)]，
    verdict ∈ {exclude, oob, out}；判定顺序=先 include 命中，再 exclude 命中即拒。"""
    seen, out = set(), []
    for h in extract_hosts(args):
        if h not in seen:
            seen.add(h)
            v = scope_verdict(h, scope)
            if v != "in":
                out.append((h, v))
    return out


def _looks_host(s):
    """候选是否为主机形态（域名/IPv4/IPv6/localhost）；非主机 token 一律不提取。"""
    if not s or s != s.strip() or chr(92) in s or "=" in s:
        return False
    if s == "localhost":
        return True
    if _IPV4_RE.match(s):
        return True
    if s.count(":") >= 2:
        return bool(_IPV6_RE.match(s))  # IPv6 字面量（含 ::1）；hex 外字符=非主机
    if ":" in s:
        s = s.split(":")[0]  # host:port
    labels = [l for l in s.split(".")]
    if len(labels) < 2 or any(not l or not _LABEL_RE.match(l) for l in labels):
        return False
    return any(re.search(r"[a-z]", l, re.IGNORECASE) for l in labels)


def _hostport_of(token):
    """剥 scheme/userinfo/path/query 后的 host[:port] 段。"""
    t = token
    if "://" in t:
        t = t.split("://", 1)[1]
    if "@" in t:
        t = t.split("@")[-1]
    return re.split(r"[/?#]", t)[0].rstrip(".")


def _hosts_of_token(token):
    """单 token 的主机候选：整体段 + key=value 值段（flag 内嵌形态）。"""
    out = []
    pieces = [token]
    if "=" in token:
        pieces.append(token.split("=", 1)[1])
    for p in pieces:
        hp = _hostport_of(p)
        if hp.startswith("[") and "]" in hp:  # [IPv6]:port 括号形态
            hp = hp[1:hp.index("]")]
        elif not (hp.count(":") >= 2 and _IPV6_RE.match(hp)):
            hp = hp.split(":")[0]  # host:port 剥端口（IPv6 字面量整体保留）
        if _looks_host(hp):
            h = hp.lower()
            if h not in out:
                out.append(h)
    return out


def extract_hosts(args):
    """按出现序提取 args 中的主机（域名/IPv4/IPv6/localhost，含 flag 内嵌与
    key=value 值段、URL/userinfo/括号 IPv6 形态；代码类 token 不误判）。"""
    hosts = []
    for a in args:
        for tok in a.replace(",", " ").split():
            for h in _hosts_of_token(tok):
                if h not in hosts:
                    hosts.append(h)
    return hosts
