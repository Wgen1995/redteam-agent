# -*- coding: utf-8 -*-
"""回显入账——命令输出=证据卡+哈希锚，大输出工件化。

入账链（每一跳=账本行/卡，可回放可验真）：
  1. cmd 引用闭合（echoes 行的 cmd_id 必在 cmds.tsv 在册——回显必锚指令）；
  2. 输出全量落工件 <goal-dir>/c2/artifacts/<echo-id>.out（大输出工件化：
     全量只落工件）；
  3. 经 ledger.write_cmds._add_evidence 单源入 E-index（content_hash_raw/norm
     双指纹=norm.artifact_hashes 单源）+证据卡 evidence/<EV>.md+timeline 事件
     ——C2 回显与人工 add-evidence 同一条 13 表写路径，零第二实现；
  4. echoes.tsv 追加回显行：output_digest(sha256 全量)+evidence_id+artifact_path
     +定长摘录（大输出账内只留摘录——账本不载大块）。
"""
import hashlib
import io
import os
from contextlib import redirect_stdout

from ..ledger import core as ledger_core
from .store import C2Error, C2Store
from .tables import ECHO_ARTIFACT_THRESHOLD, EXCERPT_MAX


def _excerpt(data):
    text = data.decode("utf-8", "replace")
    if len(data) >= ECHO_ARTIFACT_THRESHOLD:
        text = text[:EXCERPT_MAX]
    return text.replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()


def submit(goal_dir, cmd_id, output, ts, note=""):
    """回显入账；返回 dict(echo_id/cmd_id/beacon_id/digest/evidence_id/...)。

    output=bytes（真身字节——哈希锚锚字节非文本解释）。cmd 不在册=拒收。
    L3 族门：c2-echo 预授权族须放行（每次执行仍入账=echoes 行本身）。
    """
    from . import families
    families.require(goal_dir, "c2-echo", ts)
    if not isinstance(output, (bytes, bytearray)):
        raise C2Error("output 须为 bytes（哈希锚锚字节——文本解释不入账）")
    output = bytes(output)
    store = C2Store(goal_dir)
    cmds = {r[0]: r for r in store.read("cmds.tsv")}
    if cmd_id not in cmds:
        raise C2Error(
            "cmd_id 引用闭合失败: %s 不在 cmds.tsv（怎么走: 先 cmd-enqueue 入队指令再回显）"
            % cmd_id)
    cmd = cmds[cmd_id]
    beacon_id = cmd[1]
    argv = cmd[2]

    echo_id = store.next_id("echoes.tsv", "ECH")
    art_rel = "c2/artifacts/%s.out" % echo_id
    art_abs = os.path.join(goal_dir, art_rel)
    os.makedirs(os.path.dirname(art_abs), exist_ok=True)
    with open(art_abs, "wb") as f:
        f.write(output)

    digest = hashlib.sha256(output).hexdigest()
    excerpt = _excerpt(output)

    # 3. 13 表单源写路径（add-evidence 同一处理器：双指纹/卡/timeline 事件/redact
    # 校验/artifact 不覆盖律全部继承——C2 面零复制账本写逻辑）。goal 锁内执行
    # ——C2 追加与 13 表写路径互斥，账本单写者纪律不破。
    from ..ledger import write_cmds
    from ..ledger.filelock import goal_lock
    rest = [
        "--title=C2 回显 %s" % cmd_id,
        "--source-type=command",
        "--observed-at=" + ts,
        "--network-position=intranet",
        "--repro-command=c2-cmd %s: %s" % (cmd_id, argv),
        "--repro-kind=single",
        "--artifact=" + art_rel,
        "--raw-excerpt=" + excerpt,
        "--timestamp=" + ts,
    ]
    buf = io.StringIO()
    try:
        with goal_lock(goal_dir):
            with redirect_stdout(buf):
                write_cmds._add_evidence(goal_dir, rest)
    except write_cmds.Reject as e:
        raise C2Error("回显证据入账被拒（add-evidence 同律）: %s" % e)

    # 读回刚落的 EV id（goal 锁内落盘后重读，尾行=刚写入行）
    ev_rows = ledger_core.Session(goal_dir).rows("E-index.tsv")
    if not ev_rows:
        raise C2Error("证据行读回失败（E-index 空——fail-closed 不造回显行）")
    evidence_id = ev_rows[-1][0]

    row = store.append("echoes.tsv", {
        "id": echo_id, "cmd_id": cmd_id, "beacon_id": beacon_id,
        "output_digest": digest, "evidence_id": evidence_id,
        "artifact_path": art_rel, "excerpt": excerpt, "ts": ts})
    return {
        "echo_id": echo_id, "cmd_id": cmd_id, "beacon_id": beacon_id,
        "digest": digest, "evidence_id": evidence_id, "artifact_path": art_rel,
        "excerpt": excerpt, "row": row, "large": len(output) >= ECHO_ARTIFACT_THRESHOLD,
    }


def echoes_for(goal_dir, cmd_id):
    """某指令的全部回显行（读面）。"""
    return [r for r in C2Store(goal_dir).read("echoes.tsv") if r[1] == cmd_id]
