// 出处:人工构造(依据 CWE-327 DES+ECB 形态)
Cipher cipher = Cipher.getInstance("DES/ECB/PKCS5Padding");
cipher.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(keyBytes, "DES"));
return cipher.doFinal(pan.getBytes());
