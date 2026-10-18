# 出处:人工构造(硬负例:结构化字段查询)
docs = db.users.find({"tenant": tenant, "status": "active"}).sort("sku", 1)
