# 出处:人工构造(依据 CWE-601 next 参数直跳)
@app.route("/after-login")
def after_login():
    return redirect(request.args.get("next", "/"))
