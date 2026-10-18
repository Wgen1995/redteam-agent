// 出处:人工构造(噪音:服务端自产常量字节流上的读点——允许命中，常量实参由 C1 反证)
byte[] FIXED = Base64.getDecoder().decode("rO0ABXNyABFjb20uYXBwLkNvbmZpZw==");
Object o = new ObjectInputStream(new ByteArrayInputStream(FIXED)).readObject();
