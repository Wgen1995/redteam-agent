# 出处:人工构造(硬负例:参数化 SQL)
rows = session.execute(text("SELECT * FROM orders WHERE tenant = :t"), {"t": tenant}).all()
