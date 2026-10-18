# 出处:人工构造(依据 CWE-918 f-string 拼接 metadata 形态)
def read_creds(path):
    r = requests.get(f"http://169.254.169.254/latest/meta-data/{path}", timeout=2)
    return r.text
