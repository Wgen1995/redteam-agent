# 出处:人工构造(依据 CWE-89 二阶:写侧入库,另一请求 ORM find_by_x 回读再拼 SQL)
@app.route("/profile", methods=["POST"])
def update_profile():
    user_repo.save(request.form)

sql = "SELECT * FROM audit WHERE note = '" + user_repo.find_by_name(name).remark + "'"
cur.execute(sql)
