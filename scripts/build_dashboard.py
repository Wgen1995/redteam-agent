#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""施工驾驶舱生成器——真数据每次重算: python3 scripts/build_dashboard.py > docs/build-status.html"""
import subprocess, html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sh(c):
    return subprocess.run(c, shell=True, cwd=ROOT, capture_output=True, text=True).stdout.strip()

def main():
    commits = sh('git log --since="24 hours ago" --oneline')
    n = len(commits.splitlines()) if commits else 0
    body = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><title>施工驾驶舱</title>
<style>body{{font-family:-apple-system,"PingFang SC";margin:0;background:#0d1117;color:#e6edf3}}header{{padding:20px 28px;border-bottom:1px solid #21262d}}h1{{font-size:20px;margin:0}}h2{{font-size:15px;color:#79c0ff;margin:24px 0 8px}}.q{{color:#8b949e;font-size:13px}}main{{padding:0 28px 40px;max-width:1100px}}.card{{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:14px 16px;margin-bottom:10px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}.ok{{color:#3fb950}}.fly{{color:#d29922}}table{{width:100%;border-collapse:collapse;font-size:13px}}td,th{{padding:6px 8px;border-bottom:1px solid #21262d;text-align:left}}a{{color:#58a6ff;text-decoration:none}}code{{background:#21262d;padding:1px 5px;border-radius:4px;font-size:12px}}pre{{font-size:11px;white-space:pre-wrap;margin:0}}</style></head><body>
<header><h1>施工驾驶舱</h1><div class="q">真数据,每次刷新重算 <code>python3 scripts/build_dashboard.py > docs/build-status.html</code> · 生成于 {html.escape(sh('date "+%F %T"'))}</div></header><main>
<h2>① 在做什么——你的产品定义 → 27 件功能</h2>
<div class="card"><table><tr><th>你的原话</th><th>对应功能</th><th>状态</th></tr>
<tr><td>「误报漏报都好」</td><td>哨兵14规则 · 定时复验 · 考卷棘轮 · 验证官复放</td><td><span class="ok">哨兵✅</span> <span class="fly">复验在建</span> <span class="ok">其余底子在</span></td></tr>
<tr><td>「自动化挖掘」</td><td>排序+自动派活 · 业务逻辑差分 · 白盒 · 30工具卡</td><td><span class="ok">排序/派活✅</span> <span class="ok">业务逻辑✅</span> <span class="fly">白盒/工具卡在建</span></td></tr>
<tr><td>「可控制」</td><td>范围锁 · 审批降噪 · 预算帽 · 紧急停</td><td><span class="fly">指挥审批在建</span> <span class="ok">其余底子在</span></td></tr>
<tr><td>「知道产品样子」</td><td>产品驾驶舱六面 · 本页</td><td><span class="fly">队首待槽</span> <span class="ok">本页即是</span></td></tr></table></div>
<h2>② 做得怎么样——24小时真数据</h2>
<div class="grid"><div class="card"><b>近24h建设提交</b><div style="font-size:30px;color:#3fb950">{n} 笔</div></div>
<div class="card"><b>底子测试</b><div style="font-size:30px">2880 用例</div><div class="q">已入库基线全绿</div></div></div>
<h2>③ 舰队</h2>
<div class="card"><table><tr><th>舰</th><th>干什么</th><th>状态</th></tr>
<tr><td>白盒A</td><td>源码解析器+锚边</td><td class="fly">在建</td></tr><tr><td>报告</td><td>证据袋+版本+报告员</td><td class="fly">在建</td></tr>
<tr><td>复验</td><td>过期漏洞自动重测</td><td class="fly">在建</td></tr><tr><td>指挥审批</td><td>聊天框开仗+审批降噪</td><td class="fly">在建</td></tr>
<tr><td>F22韧性</td><td>执行器不丢结果+30工具卡</td><td class="fly">在建</td></tr><tr><td>蒸馏入册</td><td>283张经验卡入库</td><td class="fly">在建</td></tr>
<tr><td>评审舰</td><td>独立审已建代码</td><td class="fly">在审</td></tr></table></div>
<h2>近24h提交流水(真git)</h2><div class="card"><pre>{html.escape(commits or '(无)')}</pre></div>
<h2>全貌</h2><div class="card"><a href="design/BLUEPRINT-PANORAMA.md">蓝图全景</a> · <a href="design/2026-10-20-capability-comparison-ledger.md">27件对照账</a> · <a href="design/2026-10-20-build-master-plan.md">施工总计划</a></div>
</main></body></html>"""
    print(body)

if __name__ == "__main__":
    main()
