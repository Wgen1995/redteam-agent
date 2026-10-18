# 出处:人工构造(硬负例:请求头读取)
locale = request.headers.get('Accept-Language', 'en-US')
rate = float(request.headers.get('X-Rate', '1.0'))
