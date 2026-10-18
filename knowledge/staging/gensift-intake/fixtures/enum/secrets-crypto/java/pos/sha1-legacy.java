// 出处:人工构造(依据 CWE-327 SHA-1 遗留口令比对)
MessageDigest md = MessageDigest.getInstance("SHA-1");
if (hex(md.digest(input)).equals(user.getPasswordHash())) { grant(); }
