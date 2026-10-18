// 出处:人工构造(噪音:ZipInputStream 家族标记命中,落盘前 canonical 包含检查)
try (ZipInputStream zis = new ZipInputStream(Files.newInputStream(src))) {
    ZipEntry e;
    while ((e = zis.getNextEntry()) != null) {
        File out = new File(destDir + File.separator + e.getName());
        if (!out.getCanonicalPath().startsWith(destRootCanonical)) {
            continue;
        }
        Files.copy(zis, out.toPath());
    }
}
