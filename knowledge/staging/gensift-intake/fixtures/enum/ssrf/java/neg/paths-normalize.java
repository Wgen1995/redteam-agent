// 出处:人工构造(硬负例:路径规范化,无网络)
Path normalized = Paths.get(baseDir, userPath).normalize();
if (!normalized.startsWith(baseDir)) { throw new SecurityException("path traversal"); }
