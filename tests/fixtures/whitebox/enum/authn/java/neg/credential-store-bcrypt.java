// 出处:人工构造(硬负例:口令安全存储——bcrypt 编码,认证实现正确侧)
public class CredentialStore {
    public String encode(String raw) {
        return passwordEncoder.encode(raw);
    }
    public boolean matches(String raw, String stored) {
        return passwordEncoder.matches(raw, stored);
    }
}
