// 出处:人工构造(硬负例:Base64 是编码转换非反序列化)
byte[] raw = Base64.getDecoder().decode(payload);
