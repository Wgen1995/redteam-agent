// 出处:人工构造(硬负例:安全随机)
SecureRandom sr = new SecureRandom();
byte[] token = new byte[32];
sr.nextBytes(token);
