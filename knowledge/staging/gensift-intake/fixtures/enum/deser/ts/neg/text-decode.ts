// 出处:人工构造(硬负例:字节解码非对象反序列化)
const s = new TextDecoder().decode(buf);
