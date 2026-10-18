# -*- coding: utf-8 -*-
"""api_v2_system（T7·系统配置页）——全局配置读面+写面留位，路由
GET /api/v2/system.json。

舰间契约：本文件=本舰独写；只读投影零写入（零文件 open 依赖任务数据——
全局配置不随任务换源，禁 datetime.now，读输出确定性）；写面=留位不开
（W7 权限门后开——POST_ROUTES 恒空，POST 落 /api/v2/ 未知路由=404 如实）。
挂载=ROUTES 单源表由 include 机制（api_pages.py，UI-1 舰）分发——挂法钉在
tests/test_webui_pagespec_system.py（_V2MountHandler）：GET 过会话门。

数据单源（spec §P8-P18 系统配置页读面）：
  门禁三速度 = docs/design/gates-speed-v1.md §三速度（疾速/预授权/严审——
              设计档单源，本投影只转述并逐条带来源注，不另立第二份）；
  守卫档     = goals 强度档枚举域（model_tier strong|weak / guard_tier
              T1|T2|T3——server._MODEL_TIERS/_GUARD_TIERS 同域，中译=
              ui-spec §P8-P18「完整/仅取证」）；
  预算默认   = contracts/01-ledger-schema.md（三元组形 token;requests;hours
              +示例 2M;50000;40+第四维空=关）+ 预算预警线 80%
              （api_v2_tasks._WARN_PCT 同域单源）；
  版本信息   = 代码常量 import 单源：server.Handler.server_version /
              ledger.schemas.SCHEMA_VERSION / warrior.WARRIOR_VERSION /
              tools.cards 卡册版本（server 为惰性 import——总装链上防环）。
"""
import os
import sys

_CLI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CLI_DIR not in sys.path:                     # server/测试同款兜底：cli/ 上 path
    sys.path.insert(0, _CLI_DIR)

from ledger import schemas as _schemas           # noqa: E402
from tools import cards as tool_cards            # noqa: E402
from warrior import WARRIOR_VERSION              # noqa: E402

ROUTE_SYSTEM = "/api/v2/system.json"
ROUTES = {ROUTE_SYSTEM: None}                    # 尾部赋真身（前向引用）
POST_ROUTES = {}                                 # 写面留位：W7 权限门后开

GATES_SOURCE = "docs/design/gates-speed-v1.md"

# 门禁三速度（设计档 §三速度 转述——人话律：不上工程代号）
_GATES = [
    {"id": "fast", "name": "疾速档",
     "rule": "授权范围内 + 只读 + 非破坏（侦察 / 枚举 / 指纹 / 找漏洞主面）",
     "decision": "零审批直接执行", "source": GATES_SOURCE},
    {"id": "pre", "name": "预授权档",
     "rule": ("高风险工具族 = 批一次放一族（边界=工具+参数范围+时长+资产范围；"
              "出界即停；每次执行仍记录在案）"),
     "decision": "族内不再逐次审批", "source": GATES_SOURCE},
    {"id": "strict", "name": "严审档",
     "rule": "范围变更 / 对外发送 / 破坏性操作",
     "decision": "永人工（法务红线）", "source": GATES_SOURCE},
]

# 守卫档（goals 强度档枚举域——server/api_v2_tasks 同域，不复制执法）
_TIERS = {
    "model_tier": {"enum": ["strong", "weak"],
                   "zh": {"strong": "完整", "weak": "仅取证"}},
    "guard_tier": {"enum": ["T1", "T2", "T3"]},
}

# 预算参数默认值（contracts/01 同域 + 预警线 80%）
_BUDGET = {
    "triple_format": "token;requests;hours",
    "example": "2M;50000;40",
    "dollar_dimension": "美元第四维默认关（goals 留空=关，开启才计量）",
    "warn_line_pct": 80,
    "source": "contracts/01-ledger-schema.md §goals.budget（预警线=任务页同域 80%）",
}


def _server_version():
    """server 版本惰性取（总装链上 api_pages 可能正在 import 本模块——
    顶层 from webui import server 会踩环；调用时 server 已就绪）。"""
    from webui import server as _srv
    return _srv.Handler.server_version


def _cards_version():
    vers = sorted({c.version for c in tool_cards.all_cards()})
    return vers[0] if len(vers) == 1 else "/".join(vers)


# ---------------------------------------------------------------- 读投影 --

def system_view(ledger_dir=None, battles_dir=None):
    """系统配置页读投影 → {gates, tiers, budget_defaults, versions, write,
    note}。全局配置零任务态（ledger/battles 入参收下不用——读面不随任务
    换源）；写面=留位（W7 权限门后开）。只读零写入。"""
    return {
        "gates": [dict(g) for g in _GATES],
        "tiers": {
            "model_tier": {"enum": list(_TIERS["model_tier"]["enum"]),
                           "zh": dict(_TIERS["model_tier"]["zh"])},
            "guard_tier": {"enum": list(_TIERS["guard_tier"]["enum"])},
            "note": "强度档随任务声明入账（goals 行）；本页读面展示枚举域。",
        },
        "budget_defaults": dict(_BUDGET),
        "versions": {
            "server": _server_version(),
            "ledger_schema": _schemas.SCHEMA_VERSION,
            "tool_cards": _cards_version(),
            "warrior": WARRIOR_VERSION,
        },
        "write": {
            "status": "reserved",
            "gate": "W7 权限门",
            "note": ("写面预留：W7 权限门落地后开放（届时改配置=带因入链，"
                     "走既有修订面）；当前本页只读。"),
        },
        "note": ("读面=门禁三速度/守卫档枚举/预算默认参数/版本信息（各块"
                 "标注单源出处）；写面在 W7 权限门后开放。"),
    }


# ---------------------------------------------------------------- 路由 --

def _system_route(query, ledger_dir=None, battles_dir=None):
    return 200, system_view(ledger_dir=ledger_dir, battles_dir=battles_dir)


ROUTES[ROUTE_SYSTEM] = _system_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
