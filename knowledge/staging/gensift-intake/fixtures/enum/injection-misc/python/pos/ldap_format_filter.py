# 出处:人工构造(依据 CWE-90 %-格式化拼接 filter)
flt = "(&(cn=%s)(mail=*))" % request.args.get("cn")
entries = conn.search_s(base, ldap.SCOPE_SUBTREE, flt)
