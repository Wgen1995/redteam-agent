// 出处:人工构造(硬负例:报文摘要计算)
MessageDigest md = MessageDigest.getInstance("SHA-256");
md.update(payload);
String hex = HexFormat.of().formatHex(md.digest());
