# -*- coding: utf-8 -*-
"""外部执行后端包（功能24a）——Backend 抽象+adapters 三件+归一入账。

对外面（import 单点）：
- base：帧协议 v1/能力协商/ExecOptions/Usage/Result/Session/Backend
- taskpack：意图 → 任务包（goal+scope+预算+红线）序列化
- dsh / claude / local：三 adapter（local=进程内自有 warrior 回环）
- ingest：外部回传 → facts/findings/budget 归一入账（走既有写入通道）

设计源：docs/design/2026-10-20-external-backend-design.md（唯一正文）。
"""
from . import base  # noqa: F401

__all__ = ["base"]
