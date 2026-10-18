# 出处:人工构造(硬负例:读侧 getattr)
region = getattr(settings, "region", "cn")
