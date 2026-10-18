// 出处:人工构造(硬负例:强摘要)
MessageDigest md = MessageDigest.getInstance("SHA-256");
byte[] digest = md.digest(payload);
