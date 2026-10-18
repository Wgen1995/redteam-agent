// 出处:人工构造(硬负例:bind 认证而非 filter 检索)
env.put(Context.SECURITY_PRINCIPAL, "uid=" + uid + ",ou=people,dc=example");
DirContext ctx = new InitialLdapContext(env, null);
