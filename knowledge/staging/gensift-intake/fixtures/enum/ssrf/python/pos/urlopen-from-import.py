# 出处:人工构造(依据 CWE-918 from-import 直呼 urlopen 形态)
from urllib.request import urlopen

def render(path):
    html = urlopen(path).read().decode("utf-8", "replace")
    return html
