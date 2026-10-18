# 出处:人工构造(依据 CWE-611 上传工件回读 ElementTree.parse)
import xml.etree.ElementTree

def ingest_upload(tmp_path):
    tree = xml.etree.ElementTree.parse(tmp_path)
    return tree.getroot().attrib
