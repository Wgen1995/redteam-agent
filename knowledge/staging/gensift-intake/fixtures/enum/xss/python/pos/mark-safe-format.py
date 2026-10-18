# 出处:人工构造(依据 CWE-79 Django mark_safe)
return mark_safe("<b>%s</b>" % user_name)
