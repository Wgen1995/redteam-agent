# 出处:人工构造(硬负例:线程启动非进程)
worker = threading.Thread(target=consume, args=(queue,))
worker.start()
