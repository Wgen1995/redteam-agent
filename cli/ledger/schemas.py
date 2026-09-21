# -*- coding: utf-8 -*-
# 13 表 schema——由 contracts/01（contracts-v2）机械生成，禁手改。
import json, os
TABLES = json.load(open(os.path.join(os.path.dirname(__file__), "schemas.json"), encoding="utf-8"))
SCHEMA_VERSION = "2"
GENESIS = "0" * 64
