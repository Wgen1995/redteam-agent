// 出处:人工构造(硬负例:读取常量归档)
try (java.util.zip.ZipInputStream zis = new java.util.zip.ZipInputStream(new java.io.FileInputStream(ARCHIVE))) {
    java.util.zip.ZipEntry e;
    while ((e = zis.getNextEntry()) != null) { total += e.getSize(); }
}
