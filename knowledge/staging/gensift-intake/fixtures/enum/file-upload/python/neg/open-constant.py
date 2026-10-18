# 出处:人工构造(硬负例:常量路径打开)
with open('/etc/app/tenants.yaml') as fh:
    tenants = yaml.safe_load(fh)
