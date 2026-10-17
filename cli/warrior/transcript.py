# -*- coding: utf-8 -*-
"""原始对话存档（W5 战士 MVP · 质量律 R4）——「LLM 录制」。

transcript 目录（<goal_dir>/transcripts/<INT-id>.jsonl）独立于账本：
- 账本=纪律事件（哈希链行，单源写方铸造）——transcript 不铸账本行、不改表；
- transcript=全对话留痕：一意图一 jsonl，append-only，跨重启续写；
- 行结构：ts/battle/warrior/intent/turn/model/role/content(+usage 可选)。

纪律：写失败不外抛（留痕 fail-open——主循环优先），但也不静默吞：异常经
on_error 回调上浮给调用方记账（默认 None 打印 stderr 一行）。
"""
import json
import os
import sys

DIR_NAME = "transcripts"


class Transcript(object):
    """一 goal_dir 一实例；record() 按 intent 分文件追加。"""

    def __init__(self, goal_dir, battle="", warrior="", on_error=None):
        self.goal_dir = goal_dir
        self.dir = os.path.join(goal_dir, DIR_NAME)
        self.battle = battle
        self.warrior = warrior
        self._on_error = on_error

    def record(self, intent, role, content, ts="", model="", turn=0,
               usage=None):
        """追加一行（append-only；文件级追加不重写既有行）。"""
        row = {"ts": ts, "battle": self.battle, "warrior": self.warrior,
               "intent": intent, "turn": turn, "model": model, "role": role,
               "content": content if isinstance(content, str) else str(content)}
        if usage is not None:
            row["usage"] = usage
        try:
            os.makedirs(self.dir, exist_ok=True)
            path = os.path.join(self.dir, intent + ".jsonl")
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError as e:
            if self._on_error is not None:
                try:
                    self._on_error(e)
                except Exception:
                    pass
            else:
                sys.stderr.write("transcript 写失败(fail-open): %s\n" % e)
