# 出处:人工构造(硬负例:JSON 解析)
import json
def parse_webhook(raw: str) -> dict:
    return json.loads(raw)
