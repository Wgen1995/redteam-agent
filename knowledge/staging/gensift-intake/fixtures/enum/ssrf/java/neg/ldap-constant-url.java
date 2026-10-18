// 出处:人工构造(硬负例:LDAP 常量地址,目录访问非 HTTP)
Hashtable<String, String> env = new Hashtable<>();
env.put(Context.PROVIDER_URL, "ldap://ldap.internal:389/ou=people,dc=example,dc=com");
DirContext ctx = new InitialDirContext(env);
