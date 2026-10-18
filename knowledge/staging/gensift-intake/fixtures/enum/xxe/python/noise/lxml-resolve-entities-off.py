# 出处:人工构造(噪音:同 API 安全用法——XMLParser(resolve_entities=False);允许命中由五步判别)
from lxml import etree

parser = etree.XMLParser(resolve_entities=False, no_network=True)

def consume(data: bytes):
    return etree.fromstring(data, parser=parser)
