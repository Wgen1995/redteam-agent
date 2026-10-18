# 出处:人工构造(硬负例:服务端生成临时文件名)
fd, path = tempfile.mkstemp(suffix='.csv', dir=TMP_DIR)
os.write(fd, payload)
