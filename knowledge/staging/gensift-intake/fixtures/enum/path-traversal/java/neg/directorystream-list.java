// 出处:人工构造(硬负例:目录枚举常量根)
try (DirectoryStream<Path> ds = Files.newDirectoryStream(Paths.get(uploadRoot))) {
    for (Path p : ds) {
        names.add(p.getFileName().toString());
    }
}
