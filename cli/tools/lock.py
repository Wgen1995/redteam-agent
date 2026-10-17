# -*- coding: utf-8 -*-
"""tools.lock 供应链锁定（W3④：版本+sha256+ECDSA 验签）。

锚定对象=卡纪律内容摘要（canonical bytes：binary/档位/限速/黑名单覆盖/revert/
示例/风险级）——注册表卡内容漂移即失配。验签单源=ledger.supply_chain
（openssl 子进程 + 纯库 ECDSA 回落；本模块不复制密码学代码，防两份漂移）。

信任锚（批次 4 先例同律）：本仓 tools.lock 用 TEST-ONLY 测试钥签名
（tests/fixtures/keys/），与生产锚 engines/nuclei/release.pub 无信任关系；
生产重签仪式=install/KEY-MANAGEMENT.md（人工离线执行、永不进仓）。
公钥解析序：TANYIN_TOOLS_PUB env → 仓内测试锚（缺=不可判 fail-closed）。
"""
import hashlib
import os

_LOCK_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOCK_PATH = os.path.join(_LOCK_DIR, "tools.lock")
_REPO_ROOT = os.path.dirname(os.path.dirname(_LOCK_DIR))
_TEST_PUB = os.path.join(_REPO_ROOT, "tests", "fixtures", "keys",
                         "test-release.pub")

FIELDS = ("name", "version", "sha256", "sig")


class LockError(Exception):
    """lock 形非法/供应链单源不可达（fail-closed）。"""


def resolve_pub(explicit=None):
    """公钥解析序：显式参 > TANYIN_TOOLS_PUB > 仓内测试锚；None=fail-closed。"""
    if explicit:
        return explicit
    env = os.environ.get("TANYIN_TOOLS_PUB", "")
    if env:
        return env
    return _TEST_PUB if os.path.exists(_TEST_PUB) else None


def canonical_card_bytes(card):
    """卡纪律内容规范串（tab 分隔；deny_extra/示例命令内嵌定界=空格与分号）。"""
    parts = [
        card.name, card.binary, card.tier, card.rate, card.risk,
        ";".join(card.deny_extra or []), card.revert,
        " ".join(card.example), card.version,
    ]
    return "\t".join(parts).encode("utf-8")


def card_digest(card):
    return hashlib.sha256(canonical_card_bytes(card)).hexdigest()


def _supply_chain():
    """ledger.supply_chain 单源装载（cli/ 在 sys.path 时可用；不可达=fail-closed）。"""
    try:
        from ledger import supply_chain
    except ImportError as e:
        raise LockError("supply_chain 单源不可达（cli/ 不在 sys.path）: %s" % e)
    return supply_chain


def load(path=None):
    """lock 载入：{name: {version, sha256, sig}}；行非四字段=LockError。"""
    path = path or DEFAULT_LOCK_PATH
    entries = {}
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if not ln.strip() or ln.startswith("#") or ln.startswith("format_version"):
                continue
            parts = ln.split("\t")
            if len(parts) != 4:
                raise LockError("tools.lock 行非四字段: %r" % ln[:60])
            entries[parts[0]] = dict(zip(FIELDS, parts))
    return entries


def write_entries(path, entries):
    """entries 落盘（make_lock/测试用；LF 无 BOM——selfcheck encoding 律）。"""
    lines = ["format_version=1"]
    for name in sorted(entries):
        e = entries[name]
        lines.append("\t".join([name, e["version"], e["sha256"], e["sig"]]))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def _verify_entry(name, entry, pub):
    """单条验签（复用 supply_chain.verify_entry；返回 (ok, reason)）。"""
    p = resolve_pub(pub)
    if not p or not os.path.exists(p):
        return False, "公钥锚缺失（TANYIN_TOOLS_PUB 未设且测试锚不在场）"
    full = {"key": name, "version": entry.get("version", ""),
            "sha256": entry.get("sha256", ""), "sig": entry.get("sig", ""),
            "commit": ""}
    try:
        return _supply_chain().verify_entry(full, p)
    except LockError as e:
        return False, str(e)


def verify_card(card, lock_path=None, pub=None):
    """卡级三重核：条目在场+签名有效+sha256==卡纪律内容摘要。"""
    if card is None:
        return False, "卡不存在（未注册）"
    try:
        entries = load(lock_path)
    except (OSError, LockError) as e:
        return False, "lock 载入失败（fail-closed）: %s" % e
    if card.name not in entries:
        return False, "lock 缺条目: %s（未装卡面）" % card.name
    e = entries[card.name]
    ok, why = _verify_entry(card.name, e, pub)
    if not ok:
        return False, "lock 验签失败 %s: %s" % (card.name, why)
    if e["sha256"] != card_digest(card):
        return False, "%s 卡内容 sha256 与 lock 锚不符（内容漂移）" % card.name
    return True, "ok"


def verify_all(lock_path=None, pub=None):
    """全量验签：[(name, ok, reason)]（缺条目不在结果内——逐卡核用 verify_card）。"""
    entries = load(lock_path)
    out = []
    for name in sorted(entries):
        ok, why = _verify_entry(name, entries[name], pub)
        out.append((name, ok, why))
    return out


def sign_card(card, privkey_pem):
    """发布侧签名（make_lock/测试用；运行时只验不签）。"""
    entry = {"key": card.name, "version": card.version,
             "sha256": card_digest(card), "sig": "", "commit": ""}
    return _supply_chain().sign_entry(entry, privkey_pem)
