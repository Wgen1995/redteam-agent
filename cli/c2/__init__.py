# -*- coding: utf-8 -*-
"""C2/WebShell 域账本（W3·C2-lite 账本化）——七表自持 TSV 哈希链+行族投影。

模块图: tables=schema 冻结面 / store=append-only 链存储 / beacon=登记+心跳投影 /
queue=指令队列+行号游标 / echo=回显证据化 / webshell=受控档（guard deny+revert
义务）/ families=L3 预授权审批族（gates-speed 预授权档: 批一次放一族）。
设计律: docs/design/graphled-architecture-v1.md §4 + gates-speed-v1.md §6。
"""
