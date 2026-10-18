# 出处:人工构造(依据 CWE-22 拼接打开形态)
filename = request.args.get('f')
with open(UPLOAD_DIR + '/' + filename, 'rb') as fh:
    data = fh.read()
