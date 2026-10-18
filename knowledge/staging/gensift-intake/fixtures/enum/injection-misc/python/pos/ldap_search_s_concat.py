# 出处:人工构造(依据 CWE-90 python-ldap filter 拼接)
conn = ldap.initialize("ldap://dir.example")
results = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, f"(&(uid={uid})(objectClass=person))")
