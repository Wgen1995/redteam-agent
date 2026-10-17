# -*- coding: utf-8 -*-
"""tools —— W3 工具卡包（蓝图 W3·B52 工具卡注册表）。

工具=数据不是代码（absorption-2026-10-17 §90 YAML 工具配方先例）：每张卡=
纪律字段齐备的数据结构（名称/档位/限速/黑名单覆盖/revert 义务/示例命令/风险级），
执行入口必过现有执法层（cli/tools/gate.py → tanyin-guard 委托 + L3 审批门挂卡），
供应链锁定=cli/tools/tools.lock（版本+sha256+ECDSA 验签，测试钥锚先例同批次 4）。
"""
from . import cards  # noqa: F401

__all__ = ["cards"]
