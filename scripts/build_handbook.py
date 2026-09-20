#!/usr/bin/env python3
# build_handbook.py — 零依赖学习手册站构建器
# 用法：
#   python3 scripts/build_handbook.py                # 构建 docs/learning/*.md -> docs/learning/html/
#   python3 scripts/build_handbook.py --check-links  # 校验 panorama/ 与 html/ 全部内链+锚点
#   python3 scripts/build_handbook.py --relink       # panorama 链接升级为锚点级（依据 anchors.json）
import os, re, sys, json, html as H

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEARN = os.path.join(BASE, 'docs', 'learning')
OUT = os.path.join(LEARN, 'html')
DOUT = os.path.join(BASE, 'docs', 'design', 'html')
PANO = os.path.join(BASE, 'panorama')

# ============ 站点配置 ============
FMT_SITE = {'generic_md': True, 'link_map': {}}

HANDBOOK = {
    'brand': '红队学习手册',
    'meta_line': '红队学习手册 · 持续更新 · 源文件 docs/learning/%s',
    'footer': '红队成长全景 · 手册站由 scripts/build_handbook.py 构建',
    'title_suffix': '· 红队学习手册',
    'sidebar_homes': [
        ('../../../panorama/index.html', '🗺️ 全景图总览'),
        ('../../../panorama/design.html', '🧩 设计'),
        ('index.html', '📚 手册首页'),
    ],
    'topnav': [
        ('../../../panorama/index.html', '🗺️ 总览'),
        ('index.html', '📚 手册'),
        ('../../../panorama/design.html', '🧩 设计'),
    ],
    'station_title': '📚 红队学习手册',
    'station_sub': '从源码审计到一人红队 · 每知识点【原理】【操作】【验证】【陷阱】四段 · 靶场练习全部核实',
    'station_search': '搜索全部章节标题（如：越权 / Kerberos / nuclei / 反序列化）…',
    'station_footer': '红队成长全景 · 手册站由 scripts/build_handbook.py 构建 · MD 源在 docs/learning/',
    'toc_label': '本卷目录',
}

DESIGN_DOCS = [
    ('2026-09-21-tanyin-v2-design', 'docs/design/2026-09-21-tanyin-v2-design.md', 'g1',
     '这一份是<b>唯一权威</b>：探隐 v2 综合设计定稿。TanYin v1 与方案 B′ 都已归档，冲突处以它为准。先读 §0 决策记录（四条拍板+十大裁决），再按 §4 账本 → §5 九门 → §8 纪律执法的顺序深入；§11 批次表是跟踪实施的进度尺。'),
    ('2026-09-20-tanyin-bprime-fusion', 'docs/design/2026-09-20-tanyin-bprime-fusion.md', 'g1',
     '401 行融合裁决，v2 的直接上游：TanYin 骨架 × B′ 门禁 × TSecBench 证据的逐项对质记录。想弄清「为什么 v2 这么定」，尤其是复杂度之辩（状态复杂度是解药、prompt 复杂度是毒药），来这里找判决书。'),
    ('REQUIREMENTS', 'docs/design/imported/TanYin/REQUIREMENTS.md', 'g2',
     'TanYin v1 需求总纲——用户诉求最高权威的原始表述。二十分钟读完，看到 v2 保留了什么（D2-D7 全部）、修订了什么（D1 宿主与形态）。读它是为了理解出发点，而不是照它实施。'),
    ('PRINCIPLES', 'docs/design/imported/TanYin/PRINCIPLES.md', 'g2',
     '488 行设计宪法：四条铁律、十二因果链、S1-S41 执行流、四级纪律八问表——v1 最厚的一份。当参考手册用：v2 每条机制几乎都能在这里找到基因；口径矛盾以 v2 消解为准。'),
    ('architecture', 'docs/design/imported/TanYin/architecture.md', 'g2',
     'v1 架构汇报稿：五层六边形与四支柱工程哲学的原始论述。适合讲清楚「这套系统为什么这么分层」时取材——v2 §3 在此基础上重排了三件咬合。'),
    ('2026-09-17-tanyin-design', 'docs/design/imported/TanYin/doc/2026-09-17-tanyin-design.md', 'g2',
     'v1 设计定稿全文（另一台电脑原作），v2 的骨架来源：12 表账本、九个 Phase 门、引擎契约的最初完整定义。阅读坐标——v2 修订集中在形态（薄 CLI）、执法（四层）与账本（13 表）。'),
    ('2026-09-18-web-blackbox-engine', 'docs/design/imported/TanYin/doc/2026-09-18-web-blackbox-engine.md', 'g2',
     '首发引擎 web-blackbox 的 v1 专项设计：CNPEN 方法论产品化为四段操作序列。v2 §6 吸收其执行协议与失败语义——写第一个引擎实现时最贴手的施工参考。'),
]

DESIGN = {
    'brand': '探隐设计文档',
    'meta_line': '探隐设计文档站 · %s',
    'footer': '红队成长全景 · 设计文档站由 scripts/build_handbook.py 构建',
    'title_suffix': '· 探隐设计文档',
    'sidebar_homes': [
        ('../../../panorama/index.html', '🗺️ 全景图总览'),
        ('../../../panorama/design.html', '🧩 设计'),
        ('../../learning/html/index.html', '📚 手册首页'),
        ('index.html', '📐 设计文档首页'),
    ],
    'topnav': [
        ('../../../panorama/index.html', '🗺️ 总览'),
        ('../../learning/html/index.html', '📚 手册'),
        ('../../../panorama/design.html', '🧩 设计'),
    ],
    'station_title': '📐 探隐设计文档站',
    'station_sub': 'TanYin v1 原稿 → 融合裁决 → v2 定稿 · 当前唯一权威：2026-09-21 v2 定稿',
    'station_search': '搜索设计章节标题（如：creds / 九门 / egress / 黄金夹具 / 批次）…',
    'station_footer': '红队成长全景 · 设计文档站 · v1 原稿保真收录 · v2 为唯一权威',
    'toc_label': '本文目录',
    'groups': [
        ('g1', '当前权威', 'v2 定稿与融合裁决——实施期间以这两份为准，冲突处以 v2 为准。'),
        ('g2', 'TanYin v1 原稿（参考）', '另一台电脑的原始设计，保真收录：理解出发点与机制基因用，口径矛盾以 v2 消解为准。'),
    ],
}

HB_GROUPS = [
    ('基础与 Web', ['VOL-01', 'VOL-02'], '立足源码审计老本行打下的地基：请求怎么看、参数怎么传、Web 漏洞怎么验证——后面所有卷都在这两卷的语言上说话。'),
    ('内网与源码', ['VOL-03', 'VOL-04'], '从边界跳进内网的地形学：域、Kerberos、横向移动；以及源码在手时怎么把审计思维变成渗透路线。'),
    ('客户端与工具', ['VOL-05', 'VOL-06'], '拿不到 Web 入口时的另一扇门：APK/小程序/客户端包的取证式拆解；再配一把称手的工具兵器谱。'),
    ('方法论与报告', ['VOL-07-08'], '把散招收编为交战流程：侦察到报告的完整生命周期，和能让甲方点头、能让复测闭环的报告写法。'),
    ('AI 渗透三部曲', ['VOL-09A', 'VOL-09B', 'VOL-09C'], '赛道地图与项目档案 → 十大架构模式 → AI 辅助实战协作位：认识生态、吃透机制、落地到自己工作流的三步走。'),
    ('实战与行业', ['VOL-10', 'VOL-11'], '一场虚构交战的上帝视角全程实录，和零售生态（交易/促销/退款/会员/供应链五链）的行业地形——学完直接对接日常工作。'),
]

def hb_group_of(stem):
    for i, (name, vols, _) in enumerate(HB_GROUPS):
        for v in vols:
            if stem.startswith(v):
                return i
    return len(HB_GROUPS) - 1


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:#f5f3f0;color:#1f2329;line-height:1.75}
.layout{display:flex;min-height:100vh}
.sidebar{width:270px;background:#fff;border-right:1px solid #e2e8f0;padding:18px 14px;position:sticky;top:0;height:100vh;overflow:auto;flex-shrink:0}
.sidebar h3{font-size:14px;color:#b91c1c;margin-bottom:8px}
.sidebar a.home{display:block;font-size:13px;color:#475569;text-decoration:none;margin-bottom:10px;padding:6px 8px;border-radius:6px}
.sidebar a.home:hover{background:#fef2f2}
.sidebar nav a{display:block;font-size:12.5px;color:#64748b;text-decoration:none;padding:4px 8px;border-left:2px solid transparent;border-radius:0 6px 6px 0;overflow-wrap:anywhere}
.sidebar nav a.l2{font-weight:600;color:#334155;margin-top:6px}
.sidebar nav a.l3{padding-left:18px}
.sidebar nav a.l4{padding-left:30px;font-size:12px}
.sidebar nav a:hover{color:#b91c1c;background:#fef2f2}
.sidebar nav a.on{color:#b91c1c;border-left-color:#b91c1c;background:#fef2f2;font-weight:600}
.main{flex:1;min-width:0;padding:26px 34px 80px;max-width:920px;margin:0 auto}
.topnav{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}.topnav .crumb{color:#94a3b8;font-size:12px;align-self:center;margin-left:4px}
.topnav a{background:#fff;border-radius:8px;padding:5px 11px;font-size:12.5px;color:#b91c1c;text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.05)}
.doc h1{font-size:26px;margin:6px 0 4px;color:#111827}
.doc .meta{font-size:12.5px;color:#94a3b8;margin-bottom:18px;border-bottom:1px solid #e2e8f0;padding-bottom:12px}
.doc h2{font-size:20px;margin:34px 0 12px;padding-left:12px;border-left:5px solid #b91c1c;color:#1e293b}
.doc h3{font-size:17px;margin:24px 0 10px;color:#334155}
.doc h4{font-size:15px;margin:18px 0 8px;color:#475569}
.doc p{font-size:14px;color:#374151;margin:8px 0;overflow-wrap:anywhere}
.doc ul,.doc ol{margin:8px 0 8px 24px;font-size:14px;color:#374151}
.doc li{margin:4px 0;overflow-wrap:anywhere}
.doc a{color:#b91c1c}
pre.cb{background:#0f172a;color:#e2e8f0;border-radius:10px;padding:14px 16px;overflow-x:auto;font-size:12.8px;line-height:1.6;margin:12px 0;font-family:ui-monospace,Menlo,Consolas,monospace}
pre.cb .lang{display:block;color:#64748b;font-size:12px;margin-bottom:6px}
code{background:#fee2e2;color:#991b1b;border-radius:4px;padding:1px 5px;font-size:12.8px;font-family:ui-monospace,Menlo,Consolas,monospace}
pre.cb code{background:none;color:inherit;padding:0}
.doc table{border-collapse:collapse;width:100%;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 3px 12px rgba(0,0,0,.06);font-size:13px;margin:12px 0}
.doc th,.doc td{padding:7px 11px;border-bottom:1px solid #e2e8f0;text-align:left}
.doc th{background:#f1f5f9;font-size:12px}
.doc blockquote{border-left:4px solid #b91c1c;background:#fef2f2;color:#7f1d1d;border-radius:0 8px 8px 0;padding:10px 14px;margin:10px 0;font-size:13.5px;overflow-wrap:anywhere}.guide{background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #f59e0b;border-radius:0 8px 8px 0;padding:10px 14px;margin:10px 0 18px;font-size:13.5px;color:#78350f}@media(max-width:760px){.doc table{display:block;overflow-x:auto;max-width:100%}.topnav{gap:6px}.topnav a{padding:4px 8px;font-size:12px}}
.bdg{display:inline-block;padding:0 7px;border-radius:6px;font-size:12px;font-weight:700;margin-right:4px}
.bdg-p{background:#dbeafe;color:#1e40af}.bdg-o{background:#dcfce7;color:#166534}.bdg-v{background:#fef9c3;color:#854d0e}.bdg-t{background:#fee2e2;color:#991b1b}.bdg-x{background:#f3e8ff;color:#6b21a8}
.pn{display:flex;justify-content:space-between;margin-top:44px;gap:10px}
.pn a{background:#fff;border-radius:10px;padding:10px 16px;font-size:13px;color:#b91c1c;text-decoration:none;box-shadow:0 2px 10px rgba(0,0,0,.06)}
.pn a span{display:block;font-size:12px;color:#94a3b8}
footer{text-align:center;color:#94a3b8;font-size:12px;margin-top:30px}
@media(max-width:860px){.layout{display:block}.sidebar{position:static;width:auto;height:auto;border-right:none;border-bottom:1px solid #e2e8f0}.main{padding:18px 16px 60px}}
"""

JS = """
document.addEventListener('DOMContentLoaded',function(){
  var links=[].slice.call(document.querySelectorAll('.sidebar nav a'));
  if(!links.length)return;
  var byId={};links.forEach(function(a){byId[a.getAttribute('href').slice(1)]=a;});
  var heads=Object.keys(byId).map(function(id){return document.getElementById(id);}).filter(Boolean);
  var obs=new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){
      links.forEach(function(a){a.classList.remove('on');});
      var a=byId[e.target.id]; if(a)a.classList.add('on');
    }});
  },{rootMargin:'0% 0% -80% 0%'});
  heads.forEach(function(h){obs.observe(h);});
});
"""

def slugify(text):
    s = re.sub(r'[^\w\u4e00-\u9fff]+', '-', text.strip().lower())
    s = s.strip('-')
    return s or 'sec'

def fmt(s, fname):
    s = H.escape(s, quote=False)
    codes = []
    def stash(m):
        codes.append(m.group(1)); return '\x00COD%d\x00' % (len(codes)-1)
    s = re.sub(r'`([^`]+)`', stash, s)
    def link(m):
        t, u = m.group(1), m.group(2)
        mapped = None
        for _k, _v in FMT_SITE['link_map'].items():
            if _k in u:
                mapped = _v; break
        if mapped:
            u = mapped
        elif u.endswith('.md') and FMT_SITE['generic_md']:
            u = u[:-3] + '.html'
        elif '/' not in u and '.' not in u:
            return t  # 裸词引用（如 A14）不作为链接
        ext = ' target="_blank" rel="noopener"' if u.startswith('http') else ''
        return '<a href="%s"%s>%s</a>' % (u, ext, t)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', link, s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![\w*])\*([^*\s]+)\*(?![\w*])', r'<i>\1</i>', s)
    def unstash(m):
        return '<code>%s</code>' % codes[int(m.group(1))]
    s = re.sub(r'\x00COD(\d+)\x00', unstash, s)
    s = re.sub(r'【(原理|操作|验证|陷阱|练习)】', lambda m: '<span class="bdg bdg-%s">%s</span>' % ({'原理':'p','操作':'o','验证':'v','陷阱':'t','练习':'x'}[m.group(1)], m.group(1)), s)
    return s

def parse_md(path):
    lines = open(path, encoding='utf-8').read().split('\n')
    blocks, headings = [], []
    seen = {}
    title = ''
    i, n = 0, len(lines)
    def heading(ln):
        m = re.match(r'^(#{1,4})\s+(.*)$', ln)
        return (len(m.group(1)), m.group(2).strip()) if m else None
    while i < n:
        ln = lines[i]
        if ln.strip().startswith('\x60\x60\x60'):
            lang = ln.strip()[3:].strip()
            i += 1; buf = []
            while i < n and not lines[i].strip().startswith('\x60\x60\x60'):
                buf.append(lines[i]); i += 1
            i += 1
            blocks.append(('code', lang, H.escape('\n'.join(buf), quote=False)))
            continue
        h = heading(ln)
        if h:
            lvl, text = h
            if lvl == 1 and not title:
                title = text
            sid = slugify(text)
            if sid in seen:
                seen[sid] += 1; sid = '%s-%d' % (sid, seen[sid])
            else:
                seen[sid] = 1
            headings.append({'id': sid, 'text': text, 'level': lvl})
            blocks.append(('h', lvl, sid, text))
            i += 1; continue
        if ln.strip().startswith('|') and i+1 < n and re.match(r'^\s*\|[\s:|-]+\|?\s*$', lines[i+1] if '|' in lines[i+1] else ''):
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                rows.append(cells); i += 1
            blocks.append(('table', rows))
            continue
        m = re.match(r'^\s*[-*+]\s+(.*)$', ln)
        m2 = re.match(r'^\s*(\d+)[.、)]\s+(.*)$', ln)
        if m or m2:
            items = []
            while i < n:
                mm = re.match(r'^\s*[-*+]\s+(.*)$', lines[i])
                mm2 = re.match(r'^\s*(\d+)[.、)]\s+(.*)$', lines[i])
                if mm: items.append(('ul', mm.group(1)))
                elif mm2: items.append(('ol', mm2.group(2)))
                else: break
                i += 1
            blocks.append(('list', items))
            continue
        if ln.strip().startswith('>'):
            buf = []
            while i < n and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip().lstrip('>').strip()); i += 1
            blocks.append(('quote', ' '.join(buf)))
            continue
        if re.match(r'^\s*([-*_])\s*\1\s*\1[\s\1]*$', ln):
            blocks.append(('hr',)); i += 1; continue
        if not ln.strip():
            i += 1; continue
        buf = [ln.strip()]
        i += 1
        while i < n and lines[i].strip() and not heading(lines[i]) and not lines[i].strip().startswith(('\x60\x60\x60','|','>','- ','* ','1. ')) and not re.match(r'^\s*[-*+]\s+', lines[i]) and not re.match(r'^\s*\d+[.、)]\s+', lines[i]) and not re.match(r'^\s*([-*_])\s*\1\s*\1[\s\1]*$', lines[i]):
            buf.append(lines[i].strip()); i += 1
        blocks.append(('p', ' '.join(buf)))
    return title or os.path.basename(path), blocks, headings

def render(site, out_name, title, blocks, headings, prev, nxt, guide):
    toc = []
    for hd in headings:
        if hd['level'] == 1: continue
        toc.append('<a class="l%d" href="#%s">%s</a>' % (hd['level'], hd['id'], H.escape(hd['text'])))
    body = []
    for b in blocks:
        k = b[0]
        if k == 'h':
            if b[1] == 1:
                continue
            body.append('<h%d id="%s">%s</h%d>' % (b[1], b[2], fmt(b[3], out_name), b[1]))
        elif k == 'p':
            body.append('<p>%s</p>' % fmt(b[1], out_name))
        elif k == 'code':
            lang = '<span class="lang">%s</span>' % H.escape(b[1]) if b[1] else ''
            body.append('<pre class="cb">%s<code>%s</code></pre>' % (lang, b[2]))
        elif k == 'table':
            rows = b[1]
            if len(rows) >= 2: rows = [rows[0]] + rows[2:]
            t = ['<table><thead><tr>'] + ['<th>%s</th>' % fmt(c, out_name) for c in rows[0]] + ['</tr></thead><tbody>']
            for r in rows[1:]:
                if len(r) == len(rows[0]):
                    t.append('<tr>' + ''.join('<td>%s</td>' % fmt(c, out_name) for c in r) + '</tr>')
            t.append('</tbody></table>')
            body.append(''.join(t))
        elif k == 'list':
            cur, html_buf = None, []
            for kind, item in b[1]:
                if kind != cur:
                    if cur: html_buf.append('</%s>' % cur)
                    cur = 'ul' if kind == 'ul' else 'ol'
                    html_buf.append('<%s>' % cur)
                html_buf.append('<li>%s</li>' % fmt(item, out_name))
            if cur: html_buf.append('</%s>' % cur)
            body.append(''.join(html_buf))
        elif k == 'quote':
            body.append('<blockquote>%s</blockquote>' % fmt(b[1], out_name))
        elif k == 'hr':
            body.append('<hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0">')
    pn = []
    if prev: pn.append('<a href="%s"><span>← 上一篇</span>%s</a>' % (prev[0], H.escape(prev[1])))
    else: pn.append('<span></span>')
    if nxt: pn.append('<a href="%s"><span>下一篇 →</span>%s</a>' % (nxt[0], H.escape(nxt[1])))
    else: pn.append('<span></span>')
    h1_id = next((h['id'] for h in headings if h['level'] == 1), slugify(title))
    homes = ''.join('<a class="home" href="%s">%s</a>' % (h, H.escape(t)) for h, t in site['sidebar_homes'])
    topnav = ''.join('<a href="%s">%s</a>' % (h, H.escape(t)) for h, t in site['topnav'])
    return TPL % {
        'title': H.escape(title), 'suffix': site['title_suffix'], 'css': CSS,
        'homes': homes, 'toc': '\n'.join(toc), 'topnav': topnav,
        'prev': ('<a href="%s">← %s</a>' % (prev[0], H.escape(prev[1]))) if prev else '',
        'next': ('<a href="%s">%s →</a>' % (nxt[0], H.escape(nxt[1]))) if nxt else '',
        'crumb': H.escape(title), 'h1_id': h1_id, 'h1': H.escape(title),
        'meta': site['meta_line'] % out_name,
        'guide': ('<div class="guide">🧭 <b>导读</b>：%s</div>' % guide) if guide else '',
        'body': '\n'.join(body), 'pn0': pn[0], 'pn1': pn[1],
        'footer': site['footer'], 'js': JS, 'toc_label': site.get('toc_label', '本卷目录'),
    }

TPL = '''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(title)s %(suffix)s</title><style>%(css)s</style></head><body>
<div class="layout">
<aside class="sidebar">
  %(homes)s
  <h3>%(toc_label)s</h3>
  <nav>%(toc)s</nav>
</aside>
<div class="main">
  <nav class="topnav">%(topnav)s<span class="crumb">› %(crumb)s</span></nav>
  <article class="doc">
  <h1 id="%(h1_id)s">%(h1)s</h1><div class="meta">%(meta)s</div>
  %(guide)s
  %(body)s
  <div class="pn">%(pn0)s%(pn1)s</div>
  </article>
  <footer>%(footer)s</footer>
</div></div>
<script>%(js)s</script></body></html>'''

STATION_TPL = '''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(stitle)s</title><style>%(css)s
.station{max-width:1000px;margin:0 auto;padding:26px 18px 70px}
.station h1{font-size:24px;margin:10px 0 4px}
.station .sub{color:#64748b;font-size:14px;margin-bottom:18px}
.search{width:100%%;padding:12px 16px;border:2px solid #e2e8f0;border-radius:12px;font-size:15px;margin:14px 0 6px;background:#fff}
.search:focus{outline:none;border-color:#b91c1c}
.grp{margin-top:28px}
.grp h3{font-size:17px;color:#1e293b;border-left:4px solid #b91c1c;padding-left:10px;margin-bottom:4px}
.grp .gl{color:#64748b;font-size:13px;margin-bottom:12px}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:12px}
@media(max-width:720px){.cards{grid-template-columns:1fr}}
.card{background:#fff;border-radius:12px;padding:18px;box-shadow:0 3px 14px rgba(0,0,0,.06);text-decoration:none;color:inherit;border-top:4px solid #b91c1c}
.card:hover{transform:translateY(-3px);box-shadow:0 8px 22px rgba(185,28,28,.15)}
.card h4{font-size:16px;color:#1e293b;margin-bottom:6px}
.card p{font-size:12.5px;color:#64748b;margin:0}
.card .go{margin-top:10px;font-size:12.5px;font-weight:600;color:#b91c1c}
#hits{margin-top:10px}
#hits a{display:block;background:#fff;border-radius:8px;padding:8px 12px;font-size:13px;color:#334155;text-decoration:none;margin:6px 0;box-shadow:0 2px 8px rgba(0,0,0,.05)}
#hits a b{color:#b91c1c}
#hits a span{color:#94a3b8;font-size:11.5px;margin-left:8px}
</style></head><body><div class="station">
<nav class="topnav" style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">%(tnav)s</nav>
<h1>%(stitle)s</h1>
<div class="sub">%(ssub)s</div>
<input class="search" id="q" placeholder="%(sph)s">
<div id="hits"></div>
%(groups)s
<footer style="text-align:center;color:#94a3b8;font-size:12px;margin-top:34px">%(sfoot)s</footer>
</div>
<script>
var IDX=%(idx)s;
var q=document.getElementById('q'),hits=document.getElementById('hits');
q.addEventListener('input',function(){
  var v=q.value.trim().toLowerCase();
  if(!v){hits.innerHTML='';return;}
  var out=[];
  for(var i=0;i<IDX.length&&out.length<40;i++){
    var e=IDX[i];
    if(e.t.toLowerCase().indexOf(v)>=0){
      out.push('<a href="'+e.f+'#'+e.id+'"><b>'+e.t+'</b><span>'+e.f+'</span></a>');
    }
  }
  hits.innerHTML=out.join('')||'<a>无匹配章节</a>';
});
</script></body></html>'''

def build_station(site, out_dir, groups_html, idx_search):
    tnav = ''.join('<a href="%s" style="background:#fff;border-radius:8px;padding:5px 11px;font-size:12.5px;color:#b91c1c;text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.05)">%s</a>' % (h, H.escape(t)) for h, t in site['topnav'])
    html = STATION_TPL % {
        'stitle': site['station_title'], 'css': CSS, 'tnav': tnav,
        'ssub': site['station_sub'], 'sph': site['station_search'],
        'groups': groups_html, 'idx': json.dumps(idx_search, ensure_ascii=False),
        'sfoot': site['station_footer'],
    }
    open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8').write(html)

def build_handbook():
    global FMT_SITE
    FMT_SITE = {'generic_md': True, 'link_map': {}}
    os.makedirs(OUT, exist_ok=True)
    vols = sorted(f for f in os.listdir(LEARN) if f.endswith('.md'))
    anchors = {}
    meta = []
    vol_titles = {}
    for f in vols:
        vol_titles[f] = open(os.path.join(LEARN, f), encoding='utf-8').readline().lstrip('#').strip() or f[:-3]
    for idx, f in enumerate(vols):
        path = os.path.join(LEARN, f)
        title, blocks, headings = parse_md(path)
        prev = ((vols[idx-1][:-3] + '.html'), vol_titles[vols[idx-1]]) if idx > 0 else None
        nxt = ((vols[idx+1][:-3] + '.html'), vol_titles[vols[idx+1]]) if idx+1 < len(vols) else None
        html = render(HANDBOOK, f[:-3], title, blocks, headings, prev, nxt, None)
        open(os.path.join(OUT, f[:-3] + '.html'), 'w', encoding='utf-8').write(html)
        anchors[f[:-3] + '.html'] = headings
        desc = ''
        for b in blocks:
            if b[0] == 'p' and len(b[1]) > 30: desc = b[1][:120]; break
        meta.append({'file': f[:-3] + '.html', 'title': title, 'desc': desc, 'group': hb_group_of(f[:-3])})
        print('built', f, '->', f[:-3] + '.html', '(%d headings)' % len(headings))
    json.dump(anchors, open(os.path.join(OUT, 'anchors.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    idx_search = []
    for fname, hds in anchors.items():
        for hd in hds:
            if hd['level'] <= 3:
                idx_search.append({'f': fname, 'id': hd['id'], 't': hd['text']})
    groups_html = []
    for gi, (gname, gvols, gdesc) in enumerate(HB_GROUPS):
        cards = []
        for m in meta:
            if m['group'] == gi:
                cards.append('<a class="card" href="%s"><h4>%s</h4><p>%s</p><div class="go">进入阅读 →</div></a>' % (m['file'], H.escape(m['title']), H.escape(m['desc'])))
        if cards:
            groups_html.append('<div class="grp"><h3>%s</h3><div class="gl">🧭 %s</div><div class="cards">%s</div></div>' % (H.escape(gname), H.escape(gdesc), ''.join(cards)))
    build_station(HANDBOOK, OUT, '\n'.join(groups_html), idx_search)
    print('handbook station index written (%d searchable headings, %d groups)' % (len(idx_search), len(HB_GROUPS)))

def build_design():
    global FMT_SITE
    FMT_SITE = {'generic_md': False, 'link_map': {
        '2026-09-21-tanyin-v2-design': '2026-09-21-tanyin-v2-design.html',
        '2026-09-20-tanyin-bprime-fusion': '2026-09-20-tanyin-bprime-fusion.html',
        'imported/TanYin/REQUIREMENTS.md': 'REQUIREMENTS.html',
        'imported/TanYin/PRINCIPLES.md': 'PRINCIPLES.html',
        'imported/TanYin/architecture.md': 'architecture.html',
        'imported/TanYin/doc/2026-09-17-tanyin-design.md': '2026-09-17-tanyin-design.html',
        'imported/TanYin/doc/2026-09-18-web-blackbox-engine.md': '2026-09-18-web-blackbox-engine.html',
    }}
    os.makedirs(DOUT, exist_ok=True)
    docs = DESIGN_DOCS
    anchors = {}
    titles = {}
    for out_name0, src0, _g0, _gd0 in docs:
        first = open(os.path.join(BASE, src0), encoding='utf-8').readline().lstrip('#').strip()
        titles[out_name0] = first or out_name0
    for idx, (out_name, src, grp, guide) in enumerate(docs):
        path = os.path.join(BASE, src)
        title, blocks, headings = parse_md(path)
        titles[out_name] = title
        prev = ((docs[idx-1][0] + '.html'), titles[docs[idx-1][0]]) if idx > 0 else None
        nxt = ((docs[idx+1][0] + '.html'), titles.get(docs[idx+1][0], docs[idx+1][0])) if idx+1 < len(docs) else None
        html = render(DESIGN, out_name, title, blocks, headings, prev, nxt, guide)
        open(os.path.join(DOUT, out_name + '.html'), 'w', encoding='utf-8').write(html)
        anchors[out_name + '.html'] = headings
        print('built', src, '->', out_name + '.html', '(%d headings)' % len(headings))
    json.dump(anchors, open(os.path.join(DOUT, 'anchors.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    idx_search = []
    for fname, hds in anchors.items():
        for hd in hds:
            if hd['level'] <= 3:
                idx_search.append({'f': fname, 'id': hd['id'], 't': hd['text']})
    groups_html = []
    for gkey, gname, gdesc in DESIGN['groups']:
        cards = []
        for out_name, src, grp, guide in docs:
            if grp != gkey: continue
            d = re.sub(r'<[^>]+>', '', guide)[:150]
            cards.append('<a class="card" href="%s.html"><h4>%s</h4><p>%s</p><div class="go">进入阅读 →</div></a>' % (out_name, H.escape(titles.get(out_name, out_name)), H.escape(d)))
        groups_html.append('<div class="grp"><h3>%s</h3><div class="gl">🧭 %s</div><div class="cards">%s</div></div>' % (H.escape(gname), H.escape(gdesc), ''.join(cards)))
    build_station(DESIGN, DOUT, '\n'.join(groups_html), idx_search)
    print('design station index written (%d searchable headings)' % len(idx_search))

def normalize(s):
    s = re.sub(r'(详解|手册|深读|全文|见|卷|→|--)', '', s)
    return re.sub(r'[^\\w\\u4e00-\\u9fff]', '', s.lower())

def relink():
    anchors = json.load(open(os.path.join(OUT, 'anchors.json'), encoding='utf-8'))
    for page in sorted(os.listdir(PANO)):
        if not page.endswith('.html'): continue
        p = os.path.join(PANO, page)
        src = open(p, encoding='utf-8').read()
        def find_anchor(vol, keytext):
            hds = anchors.get(vol, [])
            key = normalize(keytext)
            if not key: return None
            for hd in hds:
                if hd['level'] > 3: continue
                t = normalize(hd['text'])
                if not t: continue
                if t == key or (len(key) >= 2 and key in t) or (len(t) >= 2 and t in key):
                    return hd
            return None
        def sub(m):
            whole, href, text = m.group(0), m.group(1), m.group(2)
            mm = re.match(r'\.\./docs/learning/(VOL-[\w-]+)\.md', href)
            if not mm: return whole
            vol = mm.group(1) + '.html'
            # 优先用链接自身文本；若太弱（如"详解"），回退用整行文本
            hd = find_anchor(vol, re.sub(r'<[^>]+>', '', text))
            if hd is None:
                row = re.search(r'<tr[^>]*>(?:(?!</tr>).)*' + re.escape(whole), src, re.S)
                if row:
                    rowtext = re.sub(r'<[^>]+>', ' ', row.group(0))
                    hd = find_anchor(vol, rowtext)
            newhref = '../docs/learning/html/' + vol + ('#' + hd['id'] if hd else '')
            return whole.replace(href, newhref)
            best = None
            for hd in hds:
                if hd['level'] > 3: continue
                t = normalize(hd['text'])
                if not t: continue
                if t == key or (len(key) >= 2 and key in t) or (len(t) >= 2 and t in key):
                    best = hd; break
            newhref = '../docs/learning/html/' + vol + ('#' + best['id'] if best else '')
            return whole.replace(href, newhref)
        src2 = re.sub(r'<a\s+href="([^"]*VOL-[^"]*\.md[^"]*)"[^>]*>(.*?)</a>', sub, src, flags=re.S)
        # 其余裸 .md 链接 → .html
        src2 = re.sub(r'(href=")(\.\./docs/learning/)(VOL-[\w-]+)\.md(")', r'\1\2html/\3.html\4', src2)
        if src2 != src:
            open(p, 'w', encoding='utf-8').write(src2)
            print('relinked', page)

def check_links():
    errs = []
    root_sets = [(PANO, 'panorama'), (OUT, 'learning-html'), (DOUT, 'design-html'), (os.path.join(DOUT, '..', 'imported', 'TanYin', 'panorama'), 'tanyin-v1')]
    anchor_maps = {}
    for r2, _ in root_sets:
        ap = os.path.join(r2, 'anchors.json')
        if os.path.exists(ap):
            anchor_maps[r2] = json.load(open(ap, encoding='utf-8'))
    for root, label in root_sets:
        if not os.path.isdir(root): continue
        for page in sorted(os.listdir(root)):
            if not page.endswith('.html'): continue
            p = os.path.join(root, page)
            src = open(p, encoding='utf-8').read()
            for href in re.findall(r'href="([^"#][^"]*)"', src):
                if href.startswith(('http', 'mailto')): continue
                if "'" in href or '+' in href: continue
                frag = ''
                if '#' in href:
                    href, frag = href.split('#', 1)
                if not href: continue
                target = os.path.normpath(os.path.join(root, href))
                if not os.path.exists(target):
                    errs.append('%s/%s -> %s (missing)' % (label, page, href + ('#' + frag if frag else '')))
                    continue
                if frag and href.endswith('.html'):
                    base = os.path.basename(href)
                    anch = anchor_maps.get(os.path.dirname(target), {}).get(base)
                    if anch is not None:
                        if not any(h['id'] == frag for h in anch):
                            errs.append('%s/%s -> %s#%s (anchor missing)' % (label, page, base, frag))
                    else:
                        tsrc = open(target, encoding='utf-8').read()
                        if ('id="%s"' % frag) not in tsrc:
                            errs.append('%s/%s -> %s#%s (anchor missing)' % (label, page, base, frag))
    if errs:
        print('check-links: %d errors' % len(errs))
        for e in errs[:30]: print(' ', e)
        return 1
    print('check-links: PASS ✓')
    return 0

if __name__ == '__main__':
    if '--check-links' in sys.argv: sys.exit(check_links())
    if '--relink' in sys.argv: relink()
    else:
        build_handbook()
        build_design()
