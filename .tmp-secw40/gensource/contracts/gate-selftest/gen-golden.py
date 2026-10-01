#!/usr/bin/env python3
# 重建 expected-gate.txt：提取 gate_record.md 主表行 + 追加 gate_result: pass
# 用法：python3 gen-golden.py（需先跑一次 gate 生成 gate_record.md）
import re, os
d = os.path.dirname(os.path.abspath(__file__))
lines = open(os.path.join(d, 'fixture', 'gate_record.md'), encoding='utf-8').read().splitlines()
rows = [l for l in lines if re.match(r'^\| \d+ \|', l)]
assert len(rows) >= 50, 'unexpected row count: %d' % len(rows)
rows.append('gate_result: pass')
open(os.path.join(d, 'expected-gate.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(rows) + '\n')
print('golden rows:', len(rows))
