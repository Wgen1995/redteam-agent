// 出处:人工构造(硬负例:marshal 输出——与 unmarshal 形态易混)
ctx.createMarshaller().marshal(obj, new java.io.FileOutputStream(path));
