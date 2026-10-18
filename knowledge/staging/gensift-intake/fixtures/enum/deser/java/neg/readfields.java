// 出处:人工构造(硬负例:readFields 原始字段读取)
ObjectInputStream.GetField fields = in.readFields();
int x = fields.get("x", 0);
