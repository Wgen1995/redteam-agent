# -*- coding: utf-8 -*-
"""批次4 T8：差分样例对夹具铸造（正/负对）——复制 G-g1 起步，全经 44 面命令落账（链自洽）。

产物 tests/fixtures/diff-authz/：正对（BOLA finding+同 PG 双 EV+authz-diff: 矩阵行）
+负对（fact kind=authz 回归基线×2）+ground-truth.json（5 条 planted：3 正对标记+2 负对基线）。
Ruling：①EV 卡片由脚本在 add-evidence 后覆写富化（raw_request 分带 user/anonymous、
expected.matchers 同 marker——add-evidence 模板卡片为最小骨架）；②PG 号按 E-index
pair_group 列现序+1 铸（next-id 只扫 id 列，对 PG 前缀恒返 0001 撞既有 PG-g1-0001）；
③对照组 EV 经 --linked-finding 回链 finding（add-finding 先验 EV 存在、add-evidence
后验 finding 存在——先铸实验组 EV→finding→对照组 EV 回链，scorer 取 evidence_ids∪回链并集）；
④creds 用 kind=static-cred（kind=session 须 parent_cred——计划 STEPS 未带，static-cred
语义等价且 role 覆盖投影不依赖 kind）。"""
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli", "tanyin-ledger")
SRC = os.path.join(HERE, "fixtures", "G-g1")
DST = os.path.join(HERE, "fixtures", "diff-authz")
TS = "2026-09-24T10:00:00Z"
EP = "app.intranet/admin/api/users"


def call(*args):
    r = subprocess.run([sys.executable, CLI, args[0], "--goal-dir", DST] + list(args[1:]),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write("铸造失败 %s: %s%s" % (args[0], r.stdout, r.stderr) + chr(10))
        raise SystemExit(1)
    return r.stdout


def minted(out):
    return out.splitlines()[0].split(chr(9))[1]


def next_pg():
    rows = [l.split(chr(9)) for l in open(os.path.join(DST, "E-index.tsv"),
                                          encoding="utf-8").read().splitlines() if l]
    col = None
    from importlib import util as _u
    spec = _u.spec_from_file_location("schemas", os.path.join(ROOT, "cli", "ledger", "schemas.py"))
    schemas = _u.module_from_spec(spec)
    spec.loader.exec_module(schemas)
    col = schemas.TABLES["E-index.tsv"].index("pair_group")
    best = 0
    for r in rows:
        m = re.match(r"^PG-g1-([0-9]{4})$", r[col])
        if m:
            best = max(best, int(m.group(1)))
    return "PG-g1-%04d" % (best + 1)


def card(ev, role, lines, matchers, extractors=""):
    ext = ("  extractors:\n    - " + extractors + "\n") if extractors else ""
    return ("---\nid: %s\ntitle: 差分举证-%s\nsource_type: command\n"
            "observed_at: %s\nnetwork_position: intranet\npreconditions: []\n"
            "raw_request: |\n%s\nexpected:\n  matchers:\n%s%scleanup: ''\n"
            "pair_group: %s\nrole: %s\n---\n"
            "## 原始响应摘录（脱敏+定长）与判定依据\n%s\n"
            % (ev, role, TS, lines, matchers, ext, PG, role, lines.splitlines()[-1] if lines else ""))


def main():
    if os.path.exists(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    os.makedirs(os.path.join(DST, "art"), exist_ok=True)

    call("add-scope", "--kind=account-grant", "--matcher=app.intranet", "--account=admin",
         "--permitted-actions=read;probe", "--timestamp=" + TS)
    ast = minted(call("add-asset", "--type=endpoint", "--value=" + EP, "--meta=protected",
                      "--timestamp=" + TS))
    c_admin = minted(call("add-cred", "--kind=static-cred", "--role=admin", "--username-ref=admin1",
                          "--secret-ref={{vault:cred-2}}", "--scope-asset=" + ast,
                          "--permitted-actions=read;probe", "--timestamp=" + TS))
    c_user = minted(call("add-cred", "--kind=static-cred", "--role=user", "--username-ref=user1",
                         "--secret-ref={{vault:cred-3}}", "--scope-asset=" + ast,
                         "--permitted-actions=read", "--timestamp=" + TS))
    iid = minted(call("add-intent", "--title=authz-diff %s×user" % EP, "--engine=web-blackbox",
                      "--kind=authz-diff", "--origin=entity", "--cred=" + c_user,
                      "--detail=(%s, user) 差分对；对照=anonymous" % EP,
                      "--actions=read", "--budget-share=10k;50;0.5", "--timestamp=" + TS))
    global PG
    PG = next_pg()

    open(os.path.join(DST, "art", "diff-exp.txt"), "w", encoding="utf-8", newline="\n").write(
        "HTTP/1.1 200 OK\nContent-Type: application/json\n\n"
        "{\"errorCode\":\"00000\",\"total\":42}\n")
    open(os.path.join(DST, "art", "diff-ctrl.txt"), "w", encoding="utf-8", newline="\n").write(
        "HTTP/1.1 403 Forbidden\n\nanonymous-denied\n")
    ev_exp = minted(call("add-evidence", "--title=管理接口越权读取-实验组", "--source-type=command",
                         "--observed-at=" + TS, "--network-position=intranet",
                         "--repro-command=curl -s http://app.intranet/admin/api/users -H 'Authorization: {{vault:cred-3}}'",
                         "--repro-kind=single", "--artifact=art/diff-exp.txt",
                         "--raw-excerpt=200 OK errorCode:00000 total:42",
                         "--pair-group=" + PG, "--timestamp=" + TS))
    fd = minted(call("add-finding", "--intent-id=" + iid, "--title=admin 数据可被 user 角色读取（BOLA）",
                     "--confidence=C2", "--impact=高", "--exploitation-status=suspected",
                     "--auth-context=" + c_user,
                     "--reproducible-steps=user 会话 GET /admin/api/users→200 errorCode:00000；anonymous→403（同 PG 对照）",
                     "--affected-asset-id=" + ast, "--evidence-ids=" + ev_exp,
                     "--scope-check=in_scope", "--description-brief=差分正对：user 越权读 admin 数据",
                     "--timestamp=" + TS))
    ev_ctrl = minted(call("add-evidence", "--title=管理接口越权读取-对照组", "--source-type=command",
                          "--observed-at=" + TS, "--network-position=intranet",
                          "--repro-command=curl -s http://app.intranet/admin/api/users",
                          "--repro-kind=single", "--artifact=art/diff-ctrl.txt",
                          "--raw-excerpt=403 Forbidden anonymous-denied",
                          "--linked-finding=" + fd, "--pair-group=" + PG, "--timestamp=" + TS))

    exp_m = ("    - {type: word, words: [\"errorCode:00000\"]}\n"
             "    - {type: word, words: ['\"total\":42']}\n"
             "    - {type: status, status: [200]}\n")
    exp_x = "{type: regex, name: total, regex: ['\"total\":(\\d+)']}"
    ctrl_m = ("    - {type: word, words: [\"403\", \"anonymous-denied\"]}\n"
              "    - {type: status, status: [403]}\n")
    open(os.path.join(DST, "evidence", ev_exp + ".md"), "w", encoding="utf-8", newline="\n").write(
        card(ev_exp, "user", "  GET /admin/api/users HTTP/1.1\n  Host: app.intranet\n"
              "  Authorization: {{vault:cred-3}}", exp_m, exp_x))
    open(os.path.join(DST, "evidence", ev_ctrl + ".md"), "w", encoding="utf-8", newline="\n").write(
        card(ev_ctrl, "anonymous", "  GET /admin/api/users HTTP/1.1\n  Host: app.intranet",
              ctrl_m))

    call("add-fact", "--intent-id=" + iid, "--kind=authz", "--target=app.intranet/admin/api/roles",
         "--detail=各角色 403 一致（回归基线）", "--confidence=0.9", "--timestamp=" + TS)
    call("add-fact", "--intent-id=" + iid, "--kind=authz", "--target=app.intranet/admin/api/audit",
         "--detail=各角色 403 一致（回归基线）", "--confidence=0.9", "--timestamp=" + TS)
    call("matrix-set", "--attack-surface=web.admin-panel", "--vuln-class=authz.diff", "--state=x",
         "--reason=authz-diff: user 越权读取 admin 数据（BOLA）", "--intent-id=" + iid,
         "--timestamp=" + TS)

    gt = {"planted": [
        {"id": "POS-1", "endpoint": EP, "role": "user", "marker": "errorCode:00000"},
        {"id": "POS-2", "endpoint": EP, "role": "user", "marker": '"total":42'},
        {"id": "POS-3", "endpoint": EP, "role": "user", "marker": "anonymous-denied"},
        {"id": "NEG-1", "endpoint": "app.intranet/admin/api/roles", "role": "*",
         "marker": "", "polarity": "neg"},
        {"id": "NEG-2", "endpoint": "app.intranet/admin/api/audit", "role": "*",
         "marker": "", "polarity": "neg"},
    ]}
    open(os.path.join(DST, "ground-truth.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(gt, ensure_ascii=False, indent=1) + "\n")
    print("铸成 %s：FD=%s EV=%s/%s PG=%s INT=%s CRED=%s/%s AST=%s"
          % (DST, fd, ev_exp, ev_ctrl, PG, iid, c_admin, c_user, ast))


if __name__ == "__main__":
    main()
