// 出处:人工构造(依据 CWE-90 JNDI filter 拼接)
SearchControls sc = new SearchControls();
sc.setSearchScope(SearchControls.SUBTREE_SCOPE);
NamingEnumeration<SearchResult> rs = ctx.search(baseDn, "(&(uid=" + uid + ")(objectClass=person))", sc);
