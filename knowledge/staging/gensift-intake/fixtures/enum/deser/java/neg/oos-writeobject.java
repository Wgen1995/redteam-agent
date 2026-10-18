// 出处:人工构造(硬负例:序列化写出方向非读点)
ObjectOutputStream oos = new ObjectOutputStream(out);
oos.writeObject(session);
oos.close();
