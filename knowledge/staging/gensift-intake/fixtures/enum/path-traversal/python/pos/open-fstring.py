# 出处:人工构造(依据 CWE-22 f-string 即拼接形态)
name = request.args.get('name')
with open(f"{DOC_ROOT}/{name}") as fh:
    text = fh.read()
