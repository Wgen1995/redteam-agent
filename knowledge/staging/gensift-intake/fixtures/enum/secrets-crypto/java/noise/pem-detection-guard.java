// 出处:人工构造(噪音:密钥检测器自身的判断行——允许命中)
if (input.startsWith("-----BEGIN RSA PRIVATE KEY-----")) { throw new IllegalArgumentException("key material rejected"); }
