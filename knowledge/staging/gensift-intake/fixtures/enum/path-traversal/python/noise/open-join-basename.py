# 出处:人工构造(噪音:basename 净化后同 API 用法——允许命中)
name = os.path.basename(request.args['n'])
data = open(os.path.join(ROOT, name)).read()
