# 出处:人工构造(Popen shell 管道)
subprocess.Popen("cat " + fname + " | wc -l", shell=True, stdout=subprocess.PIPE)
