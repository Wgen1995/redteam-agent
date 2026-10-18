# 出处:人工构造(依据 CWE-601 双重解码后跳转——约束与解码错位)
from urllib.parse import unquote
@app.route("/jump")
def jump():
    target = unquote(unquote(request.args.get("t", "/")))
    return redirect(target)
