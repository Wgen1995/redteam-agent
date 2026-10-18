// 出处:人工构造(噪音:MD5 作 ETag/校验和非安全语境——允许命中)
String etag = DigestUtils.md5Hex(Files.readAllBytes(path));
response.setHeader("ETag", etag);
