# 出处:人工构造(依据 CWE-918 urllib.request.urlopen 形态)
def open_remote(user_url):
    with urllib.request.urlopen(user_url) as r:
        return r.read()
