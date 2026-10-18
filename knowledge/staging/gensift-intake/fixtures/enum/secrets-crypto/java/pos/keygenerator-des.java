// 出处:人工构造(依据 CWE-327 DES 密钥生成)
KeyGenerator kg = KeyGenerator.getInstance("DES");
SecretKey k = kg.generateKey();
