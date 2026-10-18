// 出处:人工构造(硬负例:归一化后白名单内读——path-traversal 类目标)
java.nio.file.Path resolved = java.nio.file.Path.of(BASE).resolve(id + ".meta").normalize();
if (!resolved.startsWith(java.nio.file.Path.of(BASE).toRealPath())) throw new SecurityException("escape");
