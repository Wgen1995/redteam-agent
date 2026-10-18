# 出处:人工构造(依据 CWE-90 search_ext 拼接)
msgid = conn.search_ext("ou=groups,dc=example", ldap.SCOPE_ONELEVEL,
                        "(&(member=uid=" + member_id + "))", attrlist=["cn"])
