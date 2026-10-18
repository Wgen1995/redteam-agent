# 出处:人工构造(check_output + shell)
ips = subprocess.check_output("dig +short " + domain, shell=True).decode()
