// 出处:人工构造(硬负例:文件写出非响应通道)
try (FileWriter fw = new FileWriter(path)) { fw.write(payload); }
