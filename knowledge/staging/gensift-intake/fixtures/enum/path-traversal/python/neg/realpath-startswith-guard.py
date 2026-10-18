# 出处:人工构造(硬负例:读前 realpath+包含检查)
p = os.path.realpath(os.path.join(ROOT, name))
if not p.startswith(ROOT):
    abort(403)
return open(p).read()
