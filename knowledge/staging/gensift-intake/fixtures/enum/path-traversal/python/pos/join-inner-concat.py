# 出处:人工构造(依据 CWE-22 join 内再拼接形态)
sub = request.form.get('sub')
target = os.path.join(BASE_DIR, sub + '/' + name)
return open(target).read()
