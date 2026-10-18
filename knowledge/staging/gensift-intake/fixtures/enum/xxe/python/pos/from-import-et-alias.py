# 出处:人工构造(依据 CWE-611 ET 别名 + ET.parse 流式读取)
from xml.etree import ElementTree as ET
import io

def walk(body: bytes):
    for _, el in ET.parse(io.BytesIO(body)).iter():
        audit(el.tag)
