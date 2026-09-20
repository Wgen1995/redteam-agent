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
PANO = os.path.join(BASE, 'panorama')

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:#f5f3f0;color:#1f2329;line-height:1.75}
.layout{display:flex;min-height:100vh}
.sidebar{width:270px;background:#fff;border-right:1px solid #e2e8f0;padding:18px 14px;position:sticky;top:0;height:100vh;overflow:auto;flex-shrink:0}
.sidebar h3{font-size:14px;color:#b91c1c;margin-bottom:8px}
.sidebar a.home{display:block;font-size:13px;color:#475569;text-decoration:none;margin-bottom:10px;padding:6px 8px;border-radius:6px}
.sidebar a.home:hover{background:#fef2f2}
.sidebar nav a{display:block;font-size:12.5px;color:#64748b;text-decoration:none;padding:4px 8px;border-left:2px solid transparent;border-radius:0 6px 6px 0}
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
.doc blockquote{border-left:4px solid #b91c1c;background:#fef2f2;color:#7f1d1d;border-radius:0 8px 8px 0;padding:10px 14px;margin:10px 0;font-size:13.5px;overflow-wrap:anywhere}@media(max-width:760px){.doc table{display:block;overflow-x:auto;max-width:100%}.topnav{gap:6px}.topnav a{padding:4px 8px;font-size:12px}}
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
        if u.endswith('.md'):
            u = u[:-3] + '.html'
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

def render(name, title, blocks, headings, prev, nxt):
    toc = []
    for hd in headings:
        if hd['level'] == 1: continue
        toc.append('<a class="l%d" href="#%s">%s</a>' % (hd['level'], hd['id'], H.escape(hd['text'])))
    body = []
    for b in blocks:
        k = b[0]
        if k == 'h':
            if b[1] == 1:
                continue  # 正文 h1 与模板标题重复：跳过（锚点由模板 h1 承载）
            body.append('<h%d id="%s">%s</h%d>' % (b[1], b[2], fmt(b[3], name), b[1]))
        elif k == 'p':
            body.append('<p>%s</p>' % fmt(b[1], name))
        elif k == 'code':
            lang = '<span class="lang">%s</span>' % H.escape(b[1]) if b[1] else ''
            body.append('<pre class="cb">%s<code>%s</code></pre>' % (lang, b[2]))
        elif k == 'table':
            rows = b[1]
            if len(rows) >= 2: rows = [rows[0]] + rows[2:]
            t = ['<table><thead><tr>'] + ['<th>%s</th>' % fmt(c, name) for c in rows[0]] + ['</tr></thead><tbody>']
            for r in rows[1:]:
                t.append('<tr>' + ''.join('<td>%s</td>' % fmt(c, name) for c in r) + '</tr>')
            t.append('</tbody></table>')
            body.append(''.join(t))
        elif k == 'list':
            cur, html_buf = None, []
            for kind, item in b[1]:
                if kind != cur:
                    if cur: html_buf.append('</%s>' % cur)
                    cur = 'ul' if kind == 'ul' else 'ol'
                    html_buf.append('<%s>' % cur)
                html_buf.append('<li>%s</li>' % fmt(item, name))
            if cur: html_buf.append('</%s>' % cur)
            body.append(''.join(html_buf))
        elif k == 'quote':
            body.append('<blockquote>%s</blockquote>' % fmt(b[1], name))
        elif k == 'hr':
            body.append('<hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0">')
    pn = []
    if prev: pn.append('<a href="%s"><span>← 上一卷</span>%s</a>' % (prev[0], H.escape(prev[1])))
    else: pn.append('<span></span>')
    if nxt: pn.append('<a href="%s"><span>下一卷 →</span>%s</a>' % (nxt[0], H.escape(nxt[1])))
    else: pn.append('<span></span>')
    h1_id = next((h['id'] for h in headings if h['level'] == 1), slugify(title))
    return '''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s · 红队学习手册</title><style>%s</style></head><body>
<div class="layout">
<aside class="sidebar">
  <a class="home" href="../../../panorama/index.html">🗺️ 全景图总览</a>
  <a class="home" href="index.html">📚 手册首页</a>
  <h3>本卷目录</h3>
  <nav>%s</nav>
</aside>
<div class="main">
  <nav class="topnav"><a href="../../../panorama/index.html">🗺️ 总览</a><a href="index.html">📚 手册</a>%s%s<span class="crumb">› %s</span></nav>
  <article class="doc">
  <h1 id="%s">%s</h1><div class="meta">红队学习手册 · 持续更新 · 源文件 docs/learning/%s</div>
  %s
  <div class="pn">%s%s</div>
  </article>
  <footer>红队成长全景 · 手册站由 scripts/build_handbook.py 构建</footer>
</div></div>
<script>%s</script></body></html>''' % (
        H.escape(title), CSS, '\n'.join(toc),
        ('<a href="%s">← %s</a>' % (prev[0], H.escape(prev[1]))) if prev else '',
        ('<a href="%s">%s →</a>' % (nxt[0], H.escape(nxt[1]))) if nxt else '',
        h1_id, H.escape(title), name, '\n'.join(body), pn[0], pn[1], JS, H.escape(title))

def build():
    os.makedirs(OUT, exist_ok=True)
    vols = sorted(f for f in os.listdir(LEARN) if f.endswith('.md'))
    anchors = {}
    meta = []
    for idx, f in enumerate(vols):
        path = os.path.join(LEARN, f)
        title, blocks, headings = parse_md(path)
        prev = ((vols[idx-1][:-3] + '.html'), vols[idx-1][:-3]) if idx > 0 else None
        nxt = ((vols[idx+1][:-3] + '.html'), vols[idx+1][:-3]) if idx+1 < len(vols) else None
        html = render(f, title, blocks, headings, prev, nxt)
        open(os.path.join(OUT, f[:-3] + '.html'), 'w', encoding='utf-8').write(html)
        anchors[f[:-3] + '.html'] = headings
        desc = ''
        for b in blocks:
            if b[0] == 'p' and len(b[1]) > 30: desc = b[1][:120]; break
        meta.append({'file': f[:-3] + '.html', 'title': title, 'desc': desc})
        print('built', f, '->', f[:-3] + '.html', '(%d headings)' % len(headings))
    json.dump(anchors, open(os.path.join(OUT, 'anchors.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    # 手册站首页（卡片 + 标题搜索）
    idx_search = []
    for fname, hds in anchors.items():
        for hd in hds:
            if hd['level'] <= 3:
                idx_search.append({'f': fname, 'id': hd['id'], 't': hd['text']})
    cards = '\n'.join('<a class="card" href="%s"><h4>%s</h4><p>%s</p><div class="go">进入阅读 →</div></a>' % (m['file'], H.escape(m['title']), H.escape(m['desc'])) for m in meta)
    station = '''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>红队学习手册</title><style>%s
.station{max-width:1000px;margin:0 auto;padding:26px 18px 70px}
.station h1{font-size:24px;margin:10px 0 4px}
.station .sub{color:#64748b;font-size:14px;margin-bottom:18px}
.search{width:100%%;padding:12px 16px;border:2px solid #e2e8f0;border-radius:12px;font-size:15px;margin:14px 0 6px;background:#fff}
.search:focus{outline:none;border-color:#b91c1c}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}
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
<nav class="topnav" style="display:flex;gap:8px;margin-bottom:12px"><a href="../../../panorama/index.html" style="background:#fff;border-radius:8px;padding:5px 11px;font-size:12.5px;color:#b91c1c;text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.05)">🗺️ 全景图总览</a></nav>
<h1>📚 红队学习手册</h1>
<div class="sub">从源码审计到一人红队 · 每知识点【原理】【操作】【验证】【陷阱】四段 · 靶场练习全部核实</div>
<input class="search" id="q" placeholder="搜索全部章节标题（如：越权 / Kerberos / nuclei / 反序列化）…">
<div id="hits"></div>
<div class="cards">%s</div>
<footer style="text-align:center;color:#94a3b8;font-size:12px;margin-top:34px">红队成长全景 · 手册站由 scripts/build_handbook.py 构建 · MD 源在 docs/learning/</footer>
</div>
<script>
var IDX=%s;
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
</script></body></html>''' % (CSS, cards, json.dumps(idx_search, ensure_ascii=False))
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(station)
    print('station index written (%d searchable headings)' % len(idx_search))

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
    anchors = json.load(open(os.path.join(OUT, 'anchors.json'), encoding='utf-8'))
    errs = []
    roots = [PANO, OUT]
    for root in roots:
        for page in sorted(os.listdir(root)):
            if not page.endswith('.html') or page == 'index.html' and root == OUT:
                pass
            if not page.endswith('.html'): continue
            p = os.path.join(root, page)
            src = open(p, encoding='utf-8').read()
            for href in re.findall(r'href="([^"#][^"]*)"', src):
                if href.startswith(('http', 'mailto')): continue
                if "'" in href or '+' in href: continue
                frag = ''
                if '#' in href:
                    href, frag = href.split('#', 1)
                target = os.path.normpath(os.path.join(root, href)) if href else p
                if not os.path.exists(target):
                    errs.append('%s: 死链 %s%s' % (page, href, '#' + frag if frag else '')); continue
                if frag:
                    tf = os.path.basename(target)
                    ids = [h['id'] for h in anchors.get(tf, [])]
                    if tf != 'index.html' and frag not in ids:
                        errs.append('%s: 锚点不存在 %s#%s' % (page, href, frag))
    print('check-links:', ('PASS ✓' if not errs else 'FAIL'))
    for e in errs: print(' ✗', e)
    return 1 if errs else 0

if __name__ == '__main__':
    if '--check-links' in sys.argv: sys.exit(check_links())
    if '--relink' in sys.argv: relink()
    else: build()
