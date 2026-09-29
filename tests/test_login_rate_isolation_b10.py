# -*- coding: utf-8 -*-
"""批次 10 T7（P2#3）：svc-login 限流写实——per-(route,method) 计数契约。

八专家渗透 P2：类级全局计数器跨端点串扰（一端连击另一端出 marker）且重放
非自包含（RATE-01 残留计数器假象）。本测=源级契约钉+语法检；行为面由
RUNBOOK compose 活体路径复验（GT 两枚 RATE 靶同口径）。"""
import ast, os, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = os.path.join(HERE, 'range', 'seed', 'svc-login', 'app.py')


class TestLoginRateIsolation(unittest.TestCase):
    def test_per_route_counter_no_shared_class_attr(self):
        src = open(SEED, encoding='utf-8').read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for t in item.targets:
                            if isinstance(t, ast.Name) and t.id == 'attempts':
                                self.fail('类级共享计数器仍在（跨端点串扰根）')
        self.assertIn('_rate = {}', src.replace('    _rate = {}', '_rate = {}'),
                      'per-(route,method) 计数字典须在')
        self.assertIn('def _bump(self, route):', src)

    def test_seed_module_parses(self):
        ast.parse(open(SEED, encoding='utf-8').read())


if __name__ == '__main__':
    unittest.main()