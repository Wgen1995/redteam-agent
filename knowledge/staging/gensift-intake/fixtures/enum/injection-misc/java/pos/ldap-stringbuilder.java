// 出处:人工构造(依据 CWE-90 StringBuilder filter 构造)
StringBuilder filter = new StringBuilder("(&(cn=").append(cn).append(")(mail=*)(objectClass=user))");
SearchControls sc = new SearchControls();
return ctx.search(userBase, filter.toString(), sc);
