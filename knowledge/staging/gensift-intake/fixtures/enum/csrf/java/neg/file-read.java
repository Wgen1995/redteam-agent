// 出处:人工构造(硬负例:固定路径资源读取)
public String loadTaxTable() throws IOException {
    return Files.readString(Path.of("/etc/app/tax2024.csv"));
}
