// 出处:人工构造(硬负例:Runtime.exec 属命令注入类)
Runtime.getRuntime().exec("gzip -d " + uploadName);
