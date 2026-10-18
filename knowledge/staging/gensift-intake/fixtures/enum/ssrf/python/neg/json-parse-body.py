# 出处:人工构造(硬负例:解析缓存响应,消费侧)
dto = json.loads(cached_text)
return dto.get("email", "")
