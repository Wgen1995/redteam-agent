# 出处:人工构造(CWE-89 ORM extra)
qs = User.objects.extra(select={"cnt": raw_sql})
