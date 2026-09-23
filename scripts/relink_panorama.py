#!/usr/bin/env python3
# relink_panorama.py — panorama → 手册站锚点级深链（最终版）
# 步骤：A) <a ... href=*.md> → html+锚点（弱文本回退行上下文）
#       B) <a ... href=*.html>（无#）→ 锚点升级
#       C) 文本节点内 VOL-XX 链接化（斜杠列表展开、嵌套锚点清理）
#       D) 目录链接 → 手册站首页
import os, re, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANO = os.path.join(BASE, 'panorama')
OUT = os.path.join(BASE, 'docs', 'learning', 'html')

anchors = json.load(open(os.path.join(OUT, 'anchors.json'), encoding='utf-8'))
prefix_map = {}
for f in anchors:
    m = re.match(r'(VOL-\d\d(?:-\d\d)?)', f)
    if m:
        prefix_map.setdefault(m.group(1), f)
        prefix_map.setdefault(m.group(1)[:6], f)

def normalize(s):
    s = re.sub(r'(详解|手册|深读|全文|见|卷|→)', '', s)
    return re.sub(r'[^\w\u4e00-\u9fff]', '', s.lower())

def find_anchor(volfile, keytext):
    key = normalize(keytext)
    if len(key) < 2:
        return None
    for hd in anchors.get(volfile, []):
        if hd['level'] > 3:
            continue
        t = normalize(hd['text'])
        if not t:
            continue
        if t == key or key in t or (len(t) >= 2 and t in key):
            return hd
    return None

def row_text(src, needle):
    row = re.search(r'<tr[^>]*>(?:(?!</tr>).)*' + re.escape(needle), src, re.S)
    if row:
        return re.sub(r'<[^>]+>', ' ', row.group(0))
    para = re.search(r'<p>(?:(?!</p>).)*' + re.escape(needle), src, re.S)
    if para:
        return re.sub(r'<[^>]+>', ' ', para.group(0))
    return None

A_MD = re.compile(r'<a[^>]*?href="(?:\.\./docs/learning/)?(VOL-[\w-]+)\.md"[^>]*>(.*?)</a>', re.S)
A_HTML = re.compile(r'<a[^>]*?href="(?:\.\./docs/learning/html/)?(VOL-[\w-]+)\.html"[^>]*>(.*?)</a>', re.S)
VOL_TOKEN = re.compile(r'(VOL-\d\d(?:-\d\d)?)')

for page in sorted(os.listdir(PANO)):
    if not page.endswith('.html'):
        continue
    p = os.path.join(PANO, page)
    src = open(p, encoding='utf-8').read()
    orig = src

    def upgrade(m, is_md):
        whole, vol, text = m.group(0), m.group(1), m.group(2)
        volfile = vol + '.html'
        if volfile not in anchors:
            return whole
        href_m = re.search(r'href="([^"]*)"', whole)
        if not is_md and '#' in href_m.group(1):
            return whole
        plain = re.sub(r'<[^>]+>', '', text)
        hd = find_anchor(volfile, plain)
        if hd is None:
            rt = row_text(src, whole)
            if rt:
                hd = find_anchor(volfile, rt)
        href = '../docs/learning/html/' + volfile + ('#' + hd['id'] if hd else '')
        return whole.replace(href_m.group(0), 'href="%s"' % href)

    src = A_MD.sub(lambda m: upgrade(m, True), src)
    src = A_HTML.sub(lambda m: upgrade(m, False), src)

    def link_token(tag):
        f = prefix_map.get(tag)
        return '<a href="../docs/learning/html/%s">%s</a>' % (f, tag) if f else tag

    # 斜杠列表单元格：>VOL-01/02/07-08< → 逐段链接
    def slash_cell(m):
        parts = m.group(1).split('/')
        out = []
        for i, part in enumerate(parts):
            if i == 0 or part.startswith('VOL-'):
                tag = part
            else:
                tag = 'VOL-' + part
            out.append(link_token(tag))
        return '>' + '/'.join(out) + '<'
    src = re.sub(r'>(VOL-\d\d(?:-\d\d)?(?:/(?:VOL-)?\d\d(?:-\d\d)?)+)<', slash_cell, src)

    # 文本节点通用 VOL-XX 链接化（只动 >...< 之间的文本；先遮罩已有锚点区间防嵌套）
    mask_store = []
    def _mask(m):
        mask_store.append(m.group(0))
        return '\x00M%d\x00' % (len(mask_store) - 1)
    masked = re.sub(r'<a [^>]*>(?:(?!</a>).)*</a>', _mask, src, flags=re.S)
    def text_node(m):
        inner = m.group(1)
        if 'href=' in inner or '<a' in inner:
            return m.group(0)
        return '>' + VOL_TOKEN.sub(lambda t: link_token(t.group(1)), inner) + '<'
    masked = re.sub(r'>([^<>]*VOL-\d\d[^<>]*)<', text_node, masked)
    src = masked.replace('\x00', '').join([]) if False else re.sub(r'\x00M(\d+)\x00', lambda m: mask_store[int(m.group(1))], masked)

    # 嵌套锚点清理：<a ...><a ...>VOL-XX</a></a> → 单层
    src = re.sub(r'<a ([^>]*)><a [^>]*>(VOL-[^<]*)</a></a>', r'<a \1>\2</a>', src)
    # 目录链接 → 手册站首页（精确形态）
    src = src.replace('href="../docs/learning/"', 'href="../docs/learning/html/index.html"')

    if src != orig:
        open(p, 'w', encoding='utf-8', newline='\n').write(src)
        print('relinked', page)
