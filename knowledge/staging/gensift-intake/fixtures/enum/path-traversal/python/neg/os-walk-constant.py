# 出处:人工构造(硬负例:常量根目录枚举)
for root, dirs, files in os.walk('/var/lib/app'):
    names.extend(files)
