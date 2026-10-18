# -*- coding: utf-8 -*-
"""功能6 业务逻辑层夹具铸造: tests/fixtures/bizlogic-keys(CRED 活链/断链+端点+挂链 findings)。

再生成: python3 tests/make_bizlogic_fixture.py(确定性: 同输入同字节)。
设计: docs/design/2026-10-20-bizlogic-layer-design.md §1 身份矩阵。
夹具语义(键位面):
  - alice(user)/bob(user)/carol(admin) 三活静态钥匙 → 三钥匙形态;
  - alice 另有活 session(parent=CRED-0001,活链)→ 身份代表取链尾会话;
  - carol 的 session 已 revoked → 排除,静态仍在;
  - bob 的 session 指向 expired 父 → 断链不取,静态兜底(chain_broken 注记);
  - dave(user) 静态 expired → 整体排除(缺第二同级钥匙的对照组用变体见测试内 stub)。
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "bizlogic-keys")

G = "bizlogic-keys"
C = "CRED-" + G
A = "AST-" + G
I = "INT-" + G

CREDS = [
    [C + "-0001", "static-cred", "user", "alice", "{{vault:cred-1}}", A + "-0001", "", "", "", "", "active", "read;probe", "", "2", "2026-10-20T09:00:00Z", ""],
    [C + "-0002", "static-cred", "user", "bob", "{{vault:cred-2}}", A + "-0001", "", "", "", "", "active", "read", "", "2", "2026-10-20T09:00:00Z", ""],
    [C + "-0003", "static-cred", "admin", "carol", "{{vault:cred-3}}", A + "-0002", "", "", "", "", "active", "read;probe;write", "", "2", "2026-10-20T09:00:00Z", ""],
    [C + "-0004", "session", "user", "alice", "{{vault:cred-4}}", A + "-0001", I + "-0001", C + "-0001", "", "", "active", "read", "登录态(活链)", "2", "2026-10-20T10:00:00Z", ""],
    [C + "-0005", "session", "admin", "carol", "{{vault:cred-5}}", A + "-0002", I + "-0001", C + "-0003", "", "", "revoked", "read", "已吊销会话", "2", "2026-10-20T10:05:00Z", ""],
    [C + "-0006", "static-cred", "user", "dave", "{{vault:cred-6}}", A + "-0001", "", "", "", "2026-10-19T00:00:00Z", "expired", "read", "过期钥匙", "2", "2026-10-18T09:00:00Z", ""],
    [C + "-0007", "session", "user", "bob", "{{vault:cred-7}}", A + "-0001", I + "-0001", C + "-0006", "", "", "active", "read", "父链过期=断链", "2", "2026-10-20T10:10:00Z", ""],
]
ASSETS = [
    [A + "-0001", "endpoint", "shop.example/orders", "", "1", "2", "2026-10-20T09:00:00Z"],
    [A + "-0002", "endpoint", "shop.example/admin/users", "", "1", "2", "2026-10-20T09:00:00Z"],
]
INTENTS = [
    [I + "-0001", "alice 弱口令落会话", "login 面 static-cred 换 session", "done", "web-blackbox", "deep-dive", "llm", "0.7", "", "shop.example+login", "1k;20;0.2", "", "", "", "", "2", "2026-10-20T09:30:00Z"],
    [I + "-0002", "orders 面×user 差分对", "(shop.example/orders, user) 差分对;对照=anonymous", "pending", "web-blackbox", "authz-diff", "entity", "", "", "-+authz-diff+shop.example/orders×user", "10k;50;0.5", "", "", "", C + "-0004", "2", "2026-10-20T10:30:00Z"],
    [I + "-0003", "orders 面×admin 差分对", "(shop.example/orders, admin) 差分对", "pending", "web-blackbox", "authz-diff", "entity", "", "", "-+authz-diff+shop.example/orders×admin", "10k;50;0.5", "", "", "", C + "-0003", "2", "2026-10-20T10:31:00Z"],
]
FINDINGS = [
    ["FD-" + G + "-0001", I + "-0002", "user 会话可读他人订单(IDOR)", "C2", "高", "suspected", C + "-0004", "shop.example/orders+idor", "", "in_scope", "差分正对", "GET /orders?user=alice->200; anon->403", A + "-0001", "EV-" + G + "-0001", "", "findings-cards/FD-" + G + "-0001.md", "active", "2", "2026-10-20T11:00:00Z"],
    ["FD-" + G + "-0002", I + "-0003", "admin 会话可读订单", "C3", "低", "suspected", "", "shop.example/orders+authz", "", "in_scope", "链断反例", "GET /orders->200", A + "-0001", "EV-" + G + "-0002", "", "findings-cards/FD-" + G + "-0002.md", "active", "2", "2026-10-20T11:01:00Z"],
]
FACTS = [
    ["F-" + G + "-0001", I + "-0002", "authz", "shop.example/admin/users", "各角色 403 一致=回归基线", "0.9", "2", "2026-10-20T11:02:00Z"],
]


def _esc(s):
    BS = chr(92)
    return "".join({BS: BS + BS, chr(9): BS + "t", chr(13): BS + "r",
                    chr(10): BS + "n", ";": BS + ";"}.get(c, c) for c in str(s))


def _write(name, rows, nfields):
    os.makedirs(FIX, exist_ok=True)
    with open(os.path.join(FIX, name), "w", encoding="utf-8", newline=chr(10)) as f:
        f.write("".join(chr(9).join(_esc(c) for c in r) + chr(10) for r in rows))
    for r in rows:
        assert len(r) == nfields, (name, len(r))


def build():
    _write("creds.tsv", CREDS, 16)
    _write("assets.tsv", ASSETS, 7)
    _write("intents.tsv", INTENTS, 17)
    _write("findings.tsv", FINDINGS, 19)
    _write("facts.tsv", FACTS, 8)
    print("built:", FIX)


if __name__ == "__main__":
    build()
