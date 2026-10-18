# 出处:人工构造(依据 CWE-611 minidom.parse 解析上传 SVG)
from xml.dom import minidom

def svg_dimensions(path):
    dom = minidom.parse(path)
    return dom.documentElement.getAttribute('width')
