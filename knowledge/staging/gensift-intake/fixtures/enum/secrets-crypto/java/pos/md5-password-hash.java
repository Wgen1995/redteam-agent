// 出处:人工构造(依据 CWE-327 MD5 用于口令哈希)
MessageDigest md = MessageDigest.getInstance("MD5");
byte[] stored = md.digest(password.getBytes(StandardCharsets.UTF_8));
userDao.saveHash(hex(stored));
