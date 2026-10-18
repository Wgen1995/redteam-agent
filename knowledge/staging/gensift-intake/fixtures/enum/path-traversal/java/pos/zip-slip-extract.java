// 出处:zip-slip(Snyk 披露,2018)
ZipEntry entry;
try (ZipInputStream zis = new ZipInputStream(new FileInputStream(archiveFile))) {
    while ((entry = zis.getNextEntry()) != null) {
        File out = new File(destDir + File.separator + entry.getName());
        Files.copy(zis, out.toPath());
    }
}
