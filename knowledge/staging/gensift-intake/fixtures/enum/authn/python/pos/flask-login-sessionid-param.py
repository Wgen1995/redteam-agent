# 出处:人工构造(依据 CWE-384 会话标识取自请求参数——固定向量)
@app.route("/login", methods=["POST"])
def login():
    sid = request.form.get("sessionid") or generate_id()
    session["sessionid"] = sid
    return jsonify(ok=True)
