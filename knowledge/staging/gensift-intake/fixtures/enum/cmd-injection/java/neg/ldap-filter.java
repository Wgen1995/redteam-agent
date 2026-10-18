// 出处:人工构造(硬负例:LDAP 过滤器拼接)
String filter = "(&(uid=" + uid + ")(ou=eng))";
ctx.search(base, filter, sc);
