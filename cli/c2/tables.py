# -*- coding: utf-8 -*-
"""C2/WebShell 账本表 schema（W3·C2-lite 账本化）——表=数据不是代码。

设计律（docs/design/graphled-architecture-v1.md §4 + gates-speed-v1.md）：
- C2 面七表=自持 TSV 哈希链，落 <goal-dir>/c2/ 下，不进 13 战表
  （13 表 schemas.json 冻结于 contracts-v2，C2 表=域账本，同律不同册）；
- 转义/哈希律与 cli.ledger.core 同源（BS->BSBS, tab->BS t, CR/LF, 分号；
  hash = sha256(prev + "|" + 除 hash 列外全字段转义 tab 连接)）——复用
  core.esc/core.row_hash 单源，本模块零第二份实现；
- 行只增不改：一切状态（心跳活性/游标/审批族/revert 义务）=行族投影
  （同 id/同键最新行胜——发现三态/意图租约/审批/域准入同构第五例）。

七表口径（每行=append-only 账本行）：
  beacons.tsv   beacon 登记+心跳行（每 beacon=账本行：上线时刻/最后心跳/
                来源意图/凭据引用；心跳超时=状态投影翻转，不改历史行）
  cmds.tsv      指令队列（指令=append-only 行；行号=物理行序=稳定游标域）
  pulls.tsv     拉取游标行（beacon 拉取=行号游标前移，最新行胜）
  echoes.tsv    回显行（命令输出=哈希锚+证据卡引用；大输出工件化）
  webshells.tsv WebShell 受控档（会话=账本行族 open→exec→close）
  reverts.tsv   持久化副作用 revert 义务登记（与工具卡 revert 列同律）
  families.tsv  L3 预授权审批族（gates-speed 预授权档：批一次放一族，
                bounds+expire，出界即停，每次执行仍入账）
  returns.tsv   靶场回传点登记（外发律白名单：仅回传点可收外发数据）
"""

# 表名 -> 列清单（列序=TSV 列序；prev_hash/hash 恒为末两列=链位）
C2_TABLES = {
    "beacons.tsv": ["id", "kind", "ts", "intent_ref", "cred_ref",
                    "host_tag", "note", "prev_hash", "hash"],
    "cmds.tsv": ["id", "beacon_id", "argv", "enqueued_at", "approval_ref",
                 "note", "prev_hash", "hash"],
    "pulls.tsv": ["id", "beacon_id", "cursor", "ts", "prev_hash", "hash"],
    "echoes.tsv": ["id", "cmd_id", "beacon_id", "output_digest", "evidence_id",
                   "artifact_path", "excerpt", "ts", "prev_hash", "hash"],
    "webshells.tsv": ["id", "kind", "ts", "url", "intent_ref", "cred_ref",
                      "cmd", "deny_check", "revert_id", "note",
                      "prev_hash", "hash"],
    "reverts.tsv": ["id", "source", "source_id", "side_effect", "revert_cmd",
                    "status", "ts", "prev_hash", "hash"],
    "families.tsv": ["id", "family", "bounds", "decision", "approver",
                     "valid_from", "valid_until", "note", "ts",
                     "prev_hash", "hash"],
    "returns.tsv": ["id", "host", "port", "note", "ts", "prev_hash", "hash"],
}

# C2 域账本子目录（<goal-dir>/c2/；.lock 复用 goal 级单写者锁——C2 行与
# 13 表写路径共用同一把锁，账本单写者纪律不破）
C2_DIRNAME = "c2"

# 回显工件化阈值（字节）：≥阈值=大输出，全量只落工件，账内只留定长摘录
ECHO_ARTIFACT_THRESHOLD = 2048
# 账内摘录定长（与 add-evidence raw_excerpt 200 字符同律，C2 面取 200）
EXCERPT_MAX = 200

# beacon 状态投影阈值（秒）：心跳超时=状态翻转
#   online: now-last_hb <= HEARTBEAT_TIMEOUT
#   stale:  HEARTBEAT_TIMEOUT < lag <= 2*HEARTBEAT_TIMEOUT
#   offline: lag > 2*HEARTBEAT_TIMEOUT（投影翻转，不改行）
HEARTBEAT_TIMEOUT = 60.0

# C2 预授权族清单（gates-speed 预授权档：L3 工具族=批一次放一族）
FAMILIES = ("c2-beacon", "c2-cmd", "c2-echo", "c2-webshell", "c2-forward")

# beacon 通信禁碰口（battle_registry 保留口同款：ZhuLong 8900/控制台 3000/
# egress 8787/8443——C2 动态口执法，命中即拒）
PORT_DENYLIST = (8900, 3000, 8787, 8443)


def cols(table):
    """表列清单（未知表=ValueError——fail-closed 防拼写漂移）。"""
    try:
        return C2_TABLES[table]
    except KeyError:
        raise ValueError("未知 C2 表: %s（在册: %s）" % (table, " ".join(sorted(C2_TABLES))))


def row_dict(table, row):
    """行列表 -> 字段字典（读面投影用；列数不符=ValueError）。"""
    c = cols(table)
    if len(row) != len(c):
        raise ValueError("%s 列数错误 %d!=%d" % (table, len(row), len(c)))
    return dict(zip(c, row))


def dict_row(table, d):
    """字段字典 -> 行列表（写面用；缺列=ValueError——缺字段不得静默空串）。"""
    c = cols(table)
    missing = [k for k in c if k not in d]
    if missing:
        raise ValueError("%s 缺字段: %s" % (table, " ".join(missing)))
    return [str(d[k]) for k in c]
