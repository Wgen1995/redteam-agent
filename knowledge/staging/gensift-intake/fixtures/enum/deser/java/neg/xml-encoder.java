// 出处:人工构造(硬负例:XMLEncoder 写出方向)
XMLEncoder enc = new XMLEncoder(out);
enc.writeObject(conf);
enc.close();
