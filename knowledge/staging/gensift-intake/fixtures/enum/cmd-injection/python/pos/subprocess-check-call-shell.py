# 出处:人工构造(check_call + shell)
subprocess.check_call("openssl dgst -sha256 " + f, shell=True)
