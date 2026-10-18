# 出处:人工构造(硬负例:名为 parse_xml 实为 JSON 的封装)
def parse_xml(payload: str):
    return json.loads(payload)
