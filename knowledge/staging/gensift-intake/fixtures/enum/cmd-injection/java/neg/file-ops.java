// 出处:人工构造(硬负例:File 删除/建目录非进程)
File out = new File(baseDir, fileName);
out.delete(); out.mkdirs();
