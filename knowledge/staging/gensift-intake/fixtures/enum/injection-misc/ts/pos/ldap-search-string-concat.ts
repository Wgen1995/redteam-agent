// 出处:人工构造(依据 CWE-90 ldapts 字符串拼接 filter)
const opts = { scope: SearchScope.Subtree, filter: "(&(cn=" + cn + "))" };
const result = await ldap.search("ou=people,dc=example", opts);
