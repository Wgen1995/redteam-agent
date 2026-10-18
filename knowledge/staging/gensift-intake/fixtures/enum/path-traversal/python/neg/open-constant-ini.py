# 出处:人工构造(硬负例:open 常量配置)
with open('/etc/app/settings.ini') as fh:
    cfg = fh.read()
