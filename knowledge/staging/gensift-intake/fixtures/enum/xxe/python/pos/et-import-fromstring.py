# 出处:人工构造(依据 CWE-611 stdlib ET.fromstring 解析请求体)
import xml.etree.ElementTree as ET
from flask import request

def parse_order():
    root = ET.fromstring(request.data)
    return root.findtext('sku')
