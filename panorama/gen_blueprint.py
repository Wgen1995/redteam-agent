#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GraphLed 蓝图生成器：panorama/blueprint.json -> panorama/graphled-blueprint.html。

修复记录（2026-10-18，全景舰）：
  1. 旧稿 CHIP 表用 \u25a1(□) 匹配"⬜"，blueprint.json 实为 U+2B1C —— 每次生成即
     KeyError 崩溃（这就是"坏稿"的病根）。现对 ✅/🔧/✈️/📐/⬜ 五态容错映射，
     未知状态归入 empty 并在终端如实披露，绝不静默丢项。
  2. 旧稿页面无导航、无互链、无生成时间 <meta>、界面芯片不计数。现与 GraphLed
     蓝图全景集七页统一暗色风（#0d1117），页首七页导航，页脚注明数据真源与再生命令。
  3. 界面计数条改为按 blueprint.json 的 ui 数组实算（当前 23 项：✅2/🔧10/✈️7/📐1/⬜3），
     柱四判词原文（"对照ARTEX 22项: 4可点/9接电/7在建/3空白"）另引一行并标出处——
     两个口径都上屏，不互相冒充。

用法：python3 panorama/gen_blueprint.py（在仓内任意目录执行均可，路径按本文件定位）
宪法口径：#41 人话（黑话首现即译）· #42 量纲（只报行数/测试数，不报时间预算）
"""
import datetime
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 五态芯片（键=blueprint.json 里的原符号；值=CSS 类名）--------------------
CHIP = {
    "\u2705": "ok",         # ✅ 可点可用
    "\U0001f527": "mount",  # 🔧 已建成,挂载中
    "\u2708\ufe0f": "fly",  # ✈️ 在建舰队
    "\U0001f4d0": "design",  # 📐 设计定稿待排
    "\u2b1c": "empty",      # ⬜ 空白（U+2B1C，旧稿误写 U+25A1 即坏因）
}
CHIP_NAME = {"ok": "可点可用", "mount": "已建成·挂载中", "fly": "在建舰队",
             "design": "设计定稿待排", "empty": "空白"}
CHIP_ORDER = ["ok", "mount", "fly", "design", "empty"]

NAV = [
    ("graphled-blueprint.html", "进度总图", True),
    ("graphled-architecture.html", "全景架构", False),
    ("graphled-ui-map.html", "界面地图", False),
    ("graphled-enemies.html", "六产品对齐", False),
    ("graphled-roadmap.html", "能力阶梯", False),
    ("graphled-methodology.html", "交战思维", False),
    ("graphled-knowledge.html", "知识全景", False),
    ("graphled-history.html", "演进总析", False),
    ("index.html", "首页", False),
]


def esc(s):
    return html.escape(str(s), quote=True)


def chip_cls(sym):
    return CHIP.get(sym, "empty")


def load():
    with open(os.path.join(HERE, "blueprint.json"), encoding="utf-8") as f:
        return json.load(f)


def nav_html():
    parts = ['<span class="brand">GraphLed 蓝图</span>']
    for href, label, on in NAV:
        parts.append('<a href="%s"%s>%s</a>' % (
            href, ' class="on"' if on else "", esc(label)))
    return '<nav class="nav">%s</nav>' % "".join(parts)


def css():
    # 旗舰视觉语言（2026-10-19 全景大合并 v2）：血缘=tanyin-architecture-v3
    # （暗底 #0d1117 + 富色彩徽章 + 分节大标题带 + 渐变点缀），禁寡灰。
    return """
*{box-sizing:border-box}body{background:#0d1117;color:#c9d1d9;margin:0;line-height:1.7;
font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1280px;margin:0 auto;padding:26px 20px 70px}
.nav{display:flex;flex-wrap:wrap;gap:6px;align-items:center;background:linear-gradient(180deg,#10161f,#0d1117);
border:1px solid #30363d;border-radius:12px;padding:9px 13px;margin-bottom:22px;position:sticky;top:0;z-index:5;
box-shadow:0 6px 22px rgba(1,4,9,.6)}
.nav .brand{font-weight:700;margin-right:8px;font-size:14px;
background:linear-gradient(90deg,#ffe9b0,#7fd49a 60%,#a5c8ff);-webkit-background-clip:text;background-clip:text;
-webkit-text-fill-color:transparent;padding-right:2px}
.nav a{color:#a5c8ff;text-decoration:none;font-size:12.5px;padding:3px 10px;border-radius:8px;border:1px solid transparent}
.nav a:hover{border-color:#58a6ff66;color:#dbe7ff}
.nav a.on{background:#0d2246;border-color:#58a6ff;color:#a5c8ff;box-shadow:0 0 12px rgba(88,166,255,.35)}
h1{color:#f0f6fc;font-size:28px;margin:2px 0 6px}
.sub{color:#8b949e;font-size:13px}
.hero{background:linear-gradient(135deg,#0d1117 0%,#0d2246 46%,#0f2e1b 100%);border:1px solid #30363d;
border-radius:14px;padding:20px 24px 16px;margin-bottom:6px;position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;top:0;left:0;right:0;height:4px;
background:linear-gradient(90deg,#e3b341,#58a6ff,#3fb950,#bc8cff)}
h2.sec{margin:34px 0 12px;padding:12px 16px 10px;border-radius:12px;position:relative;color:#e2e8f0;font-size:19px;
background:linear-gradient(90deg,#12203a 0%,#10161f 55%,#0d1117 100%);border:1px solid #26344b}
h2.sec::before{content:"";position:absolute;left:0;top:9px;bottom:9px;width:5px;border-radius:3px;
background:linear-gradient(180deg,#58a6ff,#6fc3d0)}
.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px 18px;
transition:border-color .15s,box-shadow .15s}
.card:hover{border-color:#3d4f66;box-shadow:0 8px 24px rgba(1,4,9,.5)}
.card h2{margin-top:0}
.pillars{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:900px){.pillars{grid-template-columns:1fr}}
.pillars .card{border-left:4px solid #58a6ff;background:linear-gradient(90deg,#101826,#161b22 70%)}
.pillars .card:nth-child(2){border-left-color:#e3b341}
.pillars .card:nth-child(3){border-left-color:#3fb950}
.pillars .card:nth-child(4){border-left-color:#bc8cff}
.verdict{display:inline-block;background:#3a2c0e;border:1px solid #e3b341;color:#ffe9b0;
font-size:12px;font-weight:600;border-radius:9px;padding:2px 10px;margin:2px 0 10px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{color:#a5c8ff;text-align:left;font-weight:600;background:#12203a;padding:6px 8px;border-bottom:1px solid #30363d}
td{padding:6px 8px;border-bottom:1px solid #21262d;vertical-align:top}
tr:hover td{background:#10161f}
td.st{width:34px;text-align:center;font-size:15px}
td.note{color:#8b949e;width:46%}
.chip{display:inline-flex;align-items:center;gap:6px;margin:3px;padding:4px 12px;
border:1px solid #30363d;border-radius:14px;font-size:12.5px;background:#161b22;color:#c9d1d9}
.chip i{font-style:normal}
.ok{border-color:#238636;color:#3fb950}.mount{border-color:#b08800;color:#d29922}
.fly{border-color:#1f6feb;color:#58a6ff}.design{border-color:#8957e5;color:#bc8cff}
.empty{color:#6e7681}
.lg{margin:0 14px 6px 0;font-size:12.5px;color:#8b949e;display:inline-block}
.lg i{font-style:normal;margin-right:4px}
.bar{display:flex;height:16px;border-radius:8px;overflow:hidden;border:1px solid #30363d;max-width:640px;margin:10px 0 6px}
.bar span{height:100%}
.bar .ok{background:#238636}.bar .mount{background:#b08800}.bar .fly{background:#1f6feb}
.bar .design{background:#8957e5}.bar .empty{background:#484f58}
.counts{font-size:12.5px;color:#8b949e}
ol{font-size:13.5px;line-height:2;padding-left:22px}
.meta{color:#8b949e;font-size:12px;border-top:1px solid #30363d;margin-top:42px;padding-top:12px}
.quote{border-left:3px solid #e3b341;background:#171310;border-radius:0 8px 8px 0;
padding:6px 12px;color:#cdb896;font-size:12.5px;margin:8px 0}
a{color:#58a6ff}
"""


def render(d, generated):
    # ---- 界面计数（按 ui 数组实算，不抄判词）--------------------------------
    counts = dict.fromkeys(CHIP_ORDER, 0)
    unknown = []
    chips = []
    for name, sym in d["ui"]:
        cls = chip_cls(sym)
        if sym not in CHIP:
            unknown.append(sym)
        counts[cls] += 1
        chips.append('<span class="chip %s"><i>%s</i>%s</span>' % (
            cls, esc(sym), esc(name)))
    total = sum(counts.values())

    bar = "".join('<span class="%s" style="width:%.2f%%" title="%s %d 项"></span>' % (
        k, 100.0 * counts[k] / max(total, 1), CHIP_NAME[k], counts[k])
        for k in CHIP_ORDER)
    counts_line = " · ".join("%s %d" % (CHIP_NAME[k], counts[k])
                             for k in CHIP_ORDER if counts[k])

    # ---- 四支柱 ---------------------------------------------------------------
    pillar_html = []
    for p in d["pillars"]:
        rows = "".join(
            "<tr><td>%s</td><td class='st'>%s</td><td class='note'>%s</td></tr>" % (
                esc(n), esc(s), esc(note))
            for n, s, note in p["items"])
        pillar_html.append(
            "<section class='card'><h2 style='margin-top:0'>%s</h2>"
            "<p class='verdict'>判词：%s</p><table>%s</table></section>"
            % (esc(p["name"]), esc(p["verdict"]), rows))

    legend = "".join("<span class='lg'><i>%s</i>%s</span>" % (esc(s), esc(t))
                     for s, t in d["legend"])
    nxt = "".join("<li>%s</li>" % esc(x) for x in d["next"])

    doc = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="generated" content="__GENERATED__">
<meta name="generator" content="panorama/gen_blueprint.py（数据真源=panorama/blueprint.json）">
<title>进度总图 · GraphLed 蓝图</title>
<style>__CSS__</style>
</head>
<body>
<div class="wrap">
__NAV__
<div class="hero">
<h1>进度总图 · 一页看懂建到哪了</h1>
<p class="sub">四支柱逐项对账 + 界面芯片 + 里程碑。人话口径（宪法 #41）：账本=13 张表加哈希链，是系统的唯一事实记录；挂载=页面已造好、往生产口接线的过程。数据真源=panorama/blueprint.json，零虚构。</p>
</div>

<h2 class="sec">四支柱逐项状态</h2>
<div class="pillars">__PILLARS__</div>

<h2 class="sec">界面芯片（__TOTAL__ 项，按 blueprint.json ui 数组实算）</h2>
<div class="card">
  <div class="bar">__BAR__</div>
  <div class="counts">共 __TOTAL__ 项：__COUNTS__</div>
  <div class="quote">柱四判词原文（blueprint.json）：「__VERDICT4__」——口径与 ui 数组不同（22 项 vs 23 项、可点 4 vs 2），两行都如实上屏，以 ui 数组为机器可算口径。</div>
  <div>__CHIPS__</div>
  <div style="margin-top:10px">__LEGEND__</div>
</div>

<h2 class="sec">下一步（按序）</h2>
<div class="card"><ol>__NEXT__</ol></div>

<h2 class="sec">全仓家底一句</h2>
<div class="card"><p style="margin:0;font-size:13.5px">__TESTS__</p></div>

<p class="meta">
数据真源=panorama/blueprint.json（舰队落地即更新该文件后重生成）·
本页由 panorama/gen_blueprint.py 生成于 __GENERATED__ ·
行数/测试数等实况数字另见 <a href="graphled-architecture.html">全景架构</a> 页（按仓内文件实勘）·
旧版设计图（tanyin 架构三版等）见 <a href="index.html">首页·历史档案</a>。
</p>
</div>
</body>
</html>"""
    doc = (doc
           .replace("__CSS__", css())
           .replace("__NAV__", nav_html())
           .replace("__GENERATED__", generated)
           .replace("__PILLARS__", "".join(pillar_html))
           .replace("__TOTAL__", str(total))
           .replace("__BAR__", bar)
           .replace("__COUNTS__", counts_line)
           .replace("__VERDICT4__", esc(d["pillars"][3]["verdict"]))
           .replace("__CHIPS__", "".join(chips))
           .replace("__LEGEND__", legend)
           .replace("__NEXT__", nxt)
           .replace("__TESTS__", esc(d["tests"])))
    return doc, unknown


def main():
    d = load()
    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    doc, unknown = render(d, generated)
    out = os.path.join(HERE, "graphled-blueprint.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print("regen ok:", out, len(doc), "bytes; ui items =", len(d["ui"]),
          "; unknown status symbols =", unknown or "无")


if __name__ == "__main__":
    main()
