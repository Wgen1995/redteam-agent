# 出处:人工构造(噪音:FP 卡形态——只解析服务端常量,需来源证据;命中登记)
import xml.etree.ElementTree as ET

MAPPING_XML = '<mappings><rule id="1"/></mappings>'

def load_builtin():
    return ET.fromstring(MAPPING_XML)
