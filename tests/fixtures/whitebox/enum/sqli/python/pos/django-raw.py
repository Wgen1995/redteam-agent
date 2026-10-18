# 出处:人工构造(CWE-89 Django raw % 格式化)
qs = User.objects.raw("SELECT * FROM u_user WHERE n = '%s'" % name)
