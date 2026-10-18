// 出处:人工构造(硬负例:口令存储用慢哈希)
BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(12);
String stored = encoder.encode(rawPassword);
