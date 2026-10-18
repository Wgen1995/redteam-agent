# 出处:人工构造(依据 CWE-22 join 传播形态)
data = open(os.path.join(ROOT, request.args['name'])).read()
return data
