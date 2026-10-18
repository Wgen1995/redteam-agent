// 出处:人工构造(硬负例:ProcessBuilder 属命令注入类)
new ProcessBuilder("/bin/sh", "-c", "tar czf " + file).start();
