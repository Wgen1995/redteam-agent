# 出处:人工构造(依据 CWE-611 lxml etree.parse 默认解析器)
from lxml import etree
import io

def render_feed(body: bytes):
    doc = etree.parse(io.BytesIO(body))
    return doc.xpath('/rss/channel/title/text()')
