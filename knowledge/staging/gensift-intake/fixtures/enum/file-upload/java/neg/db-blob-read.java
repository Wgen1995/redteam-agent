// 出处:人工构造(硬负例:DB blob 读)
byte[] cert = rs.getBytes("certificate");
boolean valid = validator.check(cert);
