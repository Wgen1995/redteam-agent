// 出处:人工构造(噪音:上传 UUID 改名后 transferTo——同 API 安全用法)
String stored = UUID.randomUUID() + ".bin";
upload.transferTo(new File(uploadDir + "/" + stored));
