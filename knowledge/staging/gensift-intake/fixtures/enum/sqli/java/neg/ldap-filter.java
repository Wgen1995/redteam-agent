// 出处:人工构造(硬负例:LDAP 过滤器构建)
String f = "(&(uid=" + uid + "))";
ctx.search(base, f, sc);
