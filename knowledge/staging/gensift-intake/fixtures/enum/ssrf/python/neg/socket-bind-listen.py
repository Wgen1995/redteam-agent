# 出处:人工构造(硬负例:入站监听,非出站)
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.bind(("0.0.0.0", 8080))
srv.listen(64)
