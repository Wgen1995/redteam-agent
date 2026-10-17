# -*- coding: utf-8 -*-
"""战士运行时·指令协议解析（W5 战士 MVP）。

模型输出=文本，内含 JSON 指令块（协议=SKILL.md 总控路由器的 JSON 指令块约定：
tanyin-tools exec 卡名 / tanyin-ledger 写命令 / done 终报）。解析须容错：
畸形块跳过并记错误（不炸循环），散文残留不丢（作 note 上浮）。

跑法：python3 -m unittest tests.test_warrior_protocol -v
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from warrior import protocol  # noqa: E402


class TestProtocolParse(unittest.TestCase):
    def test_bare_tool_call_parsed(self):
        r = protocol.parse('{"op":"tool","card":"dig","args":["+short","A","api.x.io"]}')
        self.assertEqual(len(r.instructions), 1)
        ins = r.instructions[0]
        self.assertEqual(ins["op"], "tool")
        self.assertEqual(ins["card"], "dig")
        self.assertEqual(ins["args"], ["+short", "A", "api.x.io"])
        self.assertEqual(r.errors, [])

    def test_fenced_json_parsed(self):
        text = '思考……执行：\n```json\n{"op":"tool","card":"curl","args":["-sS","https://a/"]}\n```\n完'
        r = protocol.parse(text)
        self.assertEqual(len(r.instructions), 1)
        self.assertEqual(r.instructions[0]["card"], "curl")

    def test_ledger_cmd_parsed_with_allowlist(self):
        r = protocol.parse('{"op":"ledger","cmd":"add-fact",'
                           '"args":{"intent-id":"INT-1","kind":"info",'
                           '"target":"x","detail":"y","confidence":"0.8"}}')
        self.assertEqual(r.instructions[0]["op"], "ledger")
        self.assertEqual(r.instructions[0]["cmd"], "add-fact")
        # 权面外命令（approve=人工权柄）解析期即拒——战士不执行权威命令
        r2 = protocol.parse('{"op":"ledger","cmd":"approve","args":{}}')
        self.assertEqual(r2.instructions, [])
        self.assertEqual(r2.errors[0]["error"], "cmd-not-allowed")

    def test_done_instruction(self):
        r = protocol.parse('{"op":"done","reason":"端口面已枚举完毕"}')
        self.assertEqual(r.instructions[0]["op"], "done")
        self.assertEqual(r.instructions[0]["reason"], "端口面已枚举完毕")

    def test_note_instruction_and_prose_kept(self):
        r = protocol.parse('前言散文。{"op":"note","text":"等待凭据"} 后记散文')
        self.assertEqual(r.instructions[0]["op"], "note")
        self.assertEqual(r.instructions[0]["text"], "等待凭据")
        self.assertIn("前言散文", r.prose)
        self.assertIn("后记散文", r.prose)

    def test_multiple_blocks_order_preserved(self):
        text = ('{"op":"tool","card":"dig","args":[]}'
                '{"op":"ledger","cmd":"add-fact","args":{}}'
                '{"op":"done","reason":"ok"}')
        r = protocol.parse(text)
        self.assertEqual([i["op"] for i in r.instructions],
                         ["tool", "ledger", "done"])

    def test_malformed_json_tolerated_good_block_survives(self):
        text = ('```json\n{"op":"tool","card":"dig", BAD}\n```\n'
                '{"op":"done","reason":"改走 done"}')
        r = protocol.parse(text)
        self.assertEqual([i["op"] for i in r.instructions], ["done"])
        self.assertEqual(len(r.errors), 1)
        self.assertEqual(r.errors[0]["error"], "bad-json")

    def test_prose_only_no_crash(self):
        r = protocol.parse("我觉得应该先做子域枚举再打面板。")
        self.assertEqual(r.instructions, [])
        self.assertEqual(r.errors, [])
        self.assertIn("子域枚举", r.prose)

    def test_unknown_op_flagged(self):
        r = protocol.parse('{"op":"delete-everything","x":1}')
        self.assertEqual(r.instructions, [])
        self.assertEqual(r.errors[0]["error"], "unknown-op")

    def test_missing_required_field_flagged(self):
        r = protocol.parse('{"op":"tool","args":[]}')   # 缺 card
        self.assertEqual(r.instructions, [])
        self.assertEqual(r.errors[0]["error"], "missing-field")

    def test_non_object_json_flagged(self):
        r = protocol.parse('[1,2,3]')
        self.assertEqual(r.instructions, [])
        self.assertEqual(r.errors[0]["error"], "not-object")

    def test_tool_args_scalar_types_only(self):
        r = protocol.parse('{"op":"tool","card":"curl","args":["-sS", 3, null]}')
        self.assertEqual(r.instructions, [])
        self.assertEqual(r.errors[0]["error"], "bad-field")


if __name__ == "__main__":
    unittest.main()
