# 出处:人工构造(硬负例:回读值仅作绑定参数,无再拼接——C4 推翻形态)
user = user_repo.find_by_name(name)
cur.execute("SELECT * FROM t WHERE u = ?", (user.remark,))
