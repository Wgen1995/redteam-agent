// 出处:人工构造(二阶:序列化 blob 落库回读形态)
byte[] blob = rs.getBytes("session_blob");
ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(blob));
SessionState st = (SessionState) ois.readObject();
