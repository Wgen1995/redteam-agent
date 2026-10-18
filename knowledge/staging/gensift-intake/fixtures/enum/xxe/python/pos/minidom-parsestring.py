# 出处:人工构造(依据 CWE-611 minidom.parseString 解析 SOAP)
from xml.dom import minidom

def soap_header(soap_body: str):
    doc = minidom.parseString(soap_body)
    return doc.getElementsByTagName('soapenv:Header')
