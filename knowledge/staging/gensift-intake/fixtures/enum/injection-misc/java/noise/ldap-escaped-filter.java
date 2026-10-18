// 出处:人工构造(噪音:RFC 4515 转义后拼接——允许命中)
String esc = LdapEncoder.filterEncode(uid);
SearchControls sc = new SearchControls();
ctx.search(base, "(&(uid=" + esc + "))", sc);
