# 出处:人工构造(硬负例:JSON 解析非数据访问)
payload = json.loads(raw_body)
event = payload.get("event", "unknown")
