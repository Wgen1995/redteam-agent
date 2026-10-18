// 出处:人工构造(硬负例:凭据散列)
public String hash(String raw) {
    byte[] d = MessageDigest.getInstance("SHA-256").digest(raw.getBytes(StandardCharsets.UTF_8));
    return Base64.getEncoder().encodeToString(d);
}
