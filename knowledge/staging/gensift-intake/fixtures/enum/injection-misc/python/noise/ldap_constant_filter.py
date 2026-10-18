# 出处:人工构造(噪音:固定 filter——允许命中)
conn = ldap.initialize("ldap://dir.example")
entries = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, "(objectClass=person)")
