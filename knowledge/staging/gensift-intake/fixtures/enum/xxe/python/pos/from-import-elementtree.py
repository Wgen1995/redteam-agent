# 出处:人工构造(依据 CWE-611 from xml.etree import ElementTree 全名形态)
from xml.etree import ElementTree

def load_report(body: bytes):
    node = ElementTree.fromstring(body)
    return {c.tag: c.text for c in node}
