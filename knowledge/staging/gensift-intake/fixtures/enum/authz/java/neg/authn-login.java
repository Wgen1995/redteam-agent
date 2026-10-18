// 出处:人工构造(硬负例:认证非授权——authn 通过不构成属主判定)
public boolean login(String username, String rawPassword) {
    String hash = credentialStore.loadHash(username);
    return passwordEncoder.matches(rawPassword, hash);
}
