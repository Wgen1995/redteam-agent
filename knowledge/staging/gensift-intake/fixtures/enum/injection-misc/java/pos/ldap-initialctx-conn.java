// 出处:人工构造(依据 CWE-90 目录上下文 + 拼接检索)
DirContext ctx = new InitialDirContext(env);
String filter = "(&(member=uid=" + memberId + ",ou=groups))";
ctx.search(groupBase, filter, null);
