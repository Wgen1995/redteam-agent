// 出处:人工构造(噪音:固定 filter 检索——允许命中)
SearchControls sc = new SearchControls();
ctx.search(baseDn, "(objectClass=person)", sc);
