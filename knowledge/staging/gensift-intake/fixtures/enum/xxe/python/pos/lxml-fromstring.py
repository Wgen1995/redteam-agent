# 出处:人工构造(依据 CWE-611 lxml 默认 resolve_entities=True 形态)
from lxml import etree

def consume_saml(response_b64: str):
    raw = base64.b64decode(response_b64)
    assertion = etree.fromstring(raw)
    return assertion.find('{urn:oasis:names:tc:SAML:2.0:assertion}NameID')
