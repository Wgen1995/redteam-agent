// 出处:人工构造(硬负例:读前 realpath+基目录包含检查，无拼接形态)
Path base = Paths.get(UPLOAD_DIR).toRealPath();
Path target = Paths.get(UPLOAD_DIR, relName).toRealPath();
if (!target.startsWith(base)) {
    throw new SecurityException("outside base");
}
byte[] data = Files.readAllBytes(target);
