# 出处:人工构造(依据 CWE-287/613 重置令牌用后不焚)
@app.route("/reset", methods=["POST"])
def do_reset():
    reset_token = request.form["token"]
    user = token_map.get(reset_token)
    user.set_password(request.form["password"])
    db.session.commit()
    return jsonify(ok=True)
