# 出处:人工构造(噪音:相对路径强校验后跳转)
def _safe(target: str) -> bool:
    return target.startswith("/") and not target.startswith("//") and "\\" not in target
@app.route("/next")
def next_page():
    to = request.args.get("to", "/dashboard")
    if not _safe(to):
        abort(400)
    return redirect(to)
