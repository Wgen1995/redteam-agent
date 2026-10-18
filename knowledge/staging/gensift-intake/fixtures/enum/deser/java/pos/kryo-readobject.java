// 出处:人工构造(依据 CWE-502 Kryo 多态根类型读点——家族标记兜住的非列举库)
Kryo kryo = new Kryo();
Object msg = kryo.readObject(input, BaseMsg.class);
