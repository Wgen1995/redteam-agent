// 出处:人工构造(依据 CWE-327 commons-codec MD5 口令比对)
String hashed = DigestUtils.md5Hex(plainPassword);
if (hashed.equals(row.get("pw"))) { loginOk(); }
