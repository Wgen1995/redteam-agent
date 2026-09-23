# -*- coding: utf-8 -*-
"""黄金夹具生成器（批次 1 T2）——确定性：固定时间戳、.example 虚构域。"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cli"))
from ledger import core

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "G-g1")
T = core.TABLES

def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r

os.makedirs(OUT, exist_ok=True)
rows = {}
rows["goals.tsv"] = [row("goals.tsv", id="G-g1-0001", target="shop.example", objective="授权渗透：商城内网分区",
    auth_doc="auth/G-g1-0001.pdf", auth_sha256="a" * 64, signer="client-cso", valid_from="2026-09-01",
    valid_until="2026-09-30", rate_limit="600/10m", window="09:00-19:00", emergency_contact="ops@example.com",
    budget="2M;50000;40", dollar_budget="0", model_tier="high", guard_tier="T3", schema_version="2",
    created="2026-09-01T09:00:00Z")]
rows["scope.tsv"] = [
    row("scope.tsv", id="S-g1-0001", kind="include", matcher="*.shop.example", note="主域及子域", schema_version="2"),
    row("scope.tsv", id="S-g1-0002", kind="include", matcher="10.10.0.0/16", note="内网分区A", account="admin;operator", permitted_actions="read;probe", schema_version="2"),
]
rows["intents.tsv"] = [
    row("intents.tsv", id="INT-g1-0001", title="子域枚举", detail="crt.sh+被动", status="done", engine="web-blackbox",
        origin="P1-recon", score="0.8", via="CNPEN-SD-01", dedup_key="sd-enumer", activation="", budget_share="0.1", schema_version="2"),
    row("intents.tsv", id="INT-g1-0002", title="admin 面板未授权访问", detail="authz-diff", status="pending",
        engine="web-blackbox", origin="P3-loop", score="", via="CNPEN-AUTH-02", dedup_key="admin-authz",
        activation="cred:CRED-g1-0001", budget_share="0.2", schema_version="2"),
]
rows["facts.tsv"] = [
    row("facts.tsv", id="F-g1-0001", intent_id="INT-g1-0001", kind="info", target="shop.example",
        detail="12 子域", confidence="0.9", schema_version="2"),
    row("facts.tsv", id="F-g1-0002", intent_id="INT-g1-0001", kind="service", target="admin-internal.shop.example",
        detail="nginx/1.25", confidence="0.9", schema_version="2"),
]
rows["findings.tsv"] = [row("findings.tsv", id="FD-g1-0001", intent_id="INT-g1-0002", title="admin 面板匿名可读",
    confidence="C3", impact="高", exploitation_status="suspected", auth_context="", dedup_key="admin-anon-read",
    scope_check="in_scope", description_brief="未登录可读订单列表", schema_version="2")]
rows["assets.tsv"] = [
    row("assets.tsv", id="AST-g1-0001", type="root-domain", value="shop.example", in_scope="1", schema_version="2"),
    row("assets.tsv", id="AST-g1-0002", type="subdomain", value="admin-internal.shop.example", in_scope="1", schema_version="2"),
    row("assets.tsv", id="AST-g1-0003", type="subdomain", value="vpn.shop.example", in_scope="0", schema_version="2"),
]
rows["edges.tsv"] = [
    row("edges.tsv", id="E-g1-0001", kind="spawns", source_id="G-g1-0001", target_id="INT-g1-0001", provenance="P1", schema_version="2"),
    row("edges.tsv", id="E-g1-0002", kind="yields", source_id="INT-g1-0001", target_id="F-g1-0001", provenance="recon", schema_version="2"),
]
rows["approvals.tsv"] = [row("approvals.tsv", id="AP-g1-0001", command_hash="b" * 64, decision="approved",
    approver="user", timestamp="2026-09-23T02:00:00Z", note="L3 高危命令", schema_version="2")]
rows["E-index.tsv"] = [row("E-index.tsv", id="EV-g1-0001", title="子域清单", source_type="command",
    observed_at="2026-09-23T01:00:00Z", network_position="internet", repro_command="curl -s https://crt.example/q?d=shop.example",
    repro_kind="single", content_hash_raw="c" * 64, content_hash_norm="d" * 64, raw_excerpt="12 subdomains",
    pair_group="PG-g1-0001", card_path="evidence/EV-g1-0001.md", schema_version="2")]
rows["matrix.tsv"] = [
    row("matrix.tsv", attack_surface="web.admin-panel", vuln_class="authn.missing", state="?", reason="", intent_id="INT-g1-0002", schema_version="2"),
    row("matrix.tsv", attack_surface="web.admin-panel", vuln_class="authz.diff", state="x", reason="FD-g1-0001", intent_id="INT-g1-0002", schema_version="2", frozen_at="2026-09-23T03:00:00Z"),
    row("matrix.tsv", attack_surface="web.api", vuln_class="inj.sql", state=" ", reason="", intent_id="", schema_version="2"),
]
rows["creds.tsv"] = [row("creds.tsv", id="CRED-g1-0001", kind="static-cred", role="admin",
    username_ref="admin", secret_ref="{{vault:cred-1}}", scope_asset="AST-g1-0002", obtained_via_intent="",
    parent_cred="", valid_until="2026-09-30", status="active", permitted_actions="read;probe", material="ntlm-hash", schema_version="2")]
rows["budget.tsv"] = [
    row("budget.tsv", timestamp="2026-09-23T01:00:00Z", token_delta="12000", requests_delta="40", hours_delta="0.2", dollars_delta="0", scope="goal", note="P1 recon", schema_version="2"),
    row("budget.tsv", timestamp="2026-09-23T02:00:00Z", token_delta="8000", requests_delta="25", hours_delta="0.1", dollars_delta="0", scope="INT-g1-0002", note="authz-diff", schema_version="2"),
]
tl = []
# 账本语义对齐（SECW-2）：行 phase 与 §5.2 门序一致——add-goal/add-scope=P0 duty；
# matrix-freeze=P2 冻结；add-fact=P3 循环；每门 duty 完成后记 gate-exit:PN 门事件
# （02a §32：门出口断言命令调用必产生 timeline 事件；asserts 数=§5.2 该门 exit 断言条数）。
events = [
    ("2026-09-23T01:00:00Z", "总控", "P0", "add-goal G-g1-0001", "irreversible"),
    ("2026-09-23T01:05:00Z", "CLI", "P0", "add-scope S-g1-0001", ""),
    ("2026-09-23T01:10:00Z", "总控", "P0", "gate-exit:P0 asserts=3 result=PASS", ""),
    ("2026-09-23T01:15:00Z", "总控", "P1", "gate-exit:P1 asserts=3 result=PASS", ""),
    ("2026-09-23T01:20:00Z", "总控", "P2", "matrix-freeze web.admin-panel/authz.diff", ""),
    ("2026-09-23T01:25:00Z", "总控", "P2", "gate-exit:P2 asserts=2 result=PASS", ""),
    ("2026-09-23T02:00:00Z", "子代理", "P3", "add-fact F-g1-0001", ""),
    ("2026-09-23T03:05:00Z", "总控", "P3", "gate-exit:P3 asserts=1 result=PASS", ""),
]
prev = core.GENESIS
for ts, actor, phase, ev, rc in events:
    wo = [ts, actor, phase, ev, rc, prev, "2"]  # 不含 hash：ts/actor/phase/ev/rc/prev/sv
    h = core.row_hash(prev, wo)
    tl.append([ts, actor, phase, ev, rc, prev, h, "2"])  # 契约列序：hash 第7、schema_version 第8
    prev = h
rows["timeline.tsv"] = tl

for tname, rr in rows.items():
    core.write_tsv(os.path.join(OUT, tname), rr)
print("fixtures:", len(rows), "tables ->", OUT)
