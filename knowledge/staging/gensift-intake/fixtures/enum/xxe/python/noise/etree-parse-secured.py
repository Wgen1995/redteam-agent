# 出处:人工构造(噪音:同 API 安全用法——硬化解析器注入 etree.parse)
from lxml import etree

secure = etree.XMLParser(resolve_entities=False, no_network=True, dtd_validation=False)

def load(path):
    return etree.parse(path, parser=secure)
