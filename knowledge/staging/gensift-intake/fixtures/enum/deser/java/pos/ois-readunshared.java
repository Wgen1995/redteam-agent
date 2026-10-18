// 出处:人工构造(依据 ObjectInputStream.readUnshared 不可共享读形态)
ObjectInputStream in = new ObjectInputStream(new FileInputStream("cache.bin"));
User u = (User) in.readUnshared();
in.close();
