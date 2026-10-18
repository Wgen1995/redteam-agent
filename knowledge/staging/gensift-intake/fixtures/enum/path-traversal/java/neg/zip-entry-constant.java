// 出处:人工构造(硬负例:ZipFile 常量条目读取)
ZipFile zf = new ZipFile(archivePath);
ZipEntry manifest = zf.getEntry("META-INF/MANIFEST.MF");
InputStream meta = zf.getInputStream(manifest);
