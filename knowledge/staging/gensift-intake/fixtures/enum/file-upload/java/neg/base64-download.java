// 出处:人工构造(硬负例:常量文件 base64 回吐)
String inline = java.util.Base64.getEncoder().encodeToString(java.nio.file.Files.readAllBytes(PLACEHOLDER));
