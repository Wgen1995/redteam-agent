# -*- coding: utf-8 -*-
"""多任务治理舰（功能25补件）包——仗间治理层。

分界声明（母舰令：你是仗间层，别重叠）：
- planner_loop（规划者舰·已落）=仗内派活——单仗 goal 目录内可达空格×五因子
  排序→add-intent 意图铸造。本包零意图铸造、零空格排序、不 import planner。
- battle_registry（W2 已落）=battles 根进程点火仲裁（registry.json：预算/
  端口/pid 收尸）。本包=舰队账面治理（fleet.tsv：状态机/士兵帽/优先级队列/
  全停阀/心跳超时）——两册并存互不代写。
- scripts/battle.py+warrior/loop.py=单仗启动与单仗循环；本包在它们之上做
  仗间调度，不代跑单仗进程。
"""
