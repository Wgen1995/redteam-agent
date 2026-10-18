// 出处:人工构造(依据 CWE-502 JDK 原生反序列化形态)
ObjectInputStream ois = new ObjectInputStream(request.getInputStream());
Object obj = ois.readObject();
ois.close();
