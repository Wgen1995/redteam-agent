// 出处:人工构造(硬负例:受难类自身钩子内字段回填，签名相似非流读点)
private void readObject(java.io.ObjectInputStream in) throws IOException, ClassNotFoundException {
    in.defaultReadObject();
}
