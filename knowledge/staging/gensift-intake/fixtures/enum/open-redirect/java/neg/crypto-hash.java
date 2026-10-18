// 出处:人工构造(硬负例:口令哈希存储是安全形态且非本类目标)
public class CredentialHasher {
    public String digest(String raw) {
        return DigestUtils.sha256Hex(raw + SALT);
    }
    public boolean matches(String raw, String stored) {
        return MessageDigest.isEqual(stored.getBytes(), digest(raw).getBytes()));
    }
}
