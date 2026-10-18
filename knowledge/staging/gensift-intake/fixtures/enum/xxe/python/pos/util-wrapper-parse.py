# 出处:人工构造(依据 CWE-611 工具类封装形态)
from lxml import etree

def safe_title(text: str) -> str:
    root = parse_xml(text)
    return (root.findtext('title') or '').strip()

def parse_xml(text):
    return etree.fromstring(text.encode('utf-8'))
