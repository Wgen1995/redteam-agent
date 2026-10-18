# 出处:人工构造(硬负例:JSON 解析)
event = json.loads(body)
sku = event.get("sku", "")
