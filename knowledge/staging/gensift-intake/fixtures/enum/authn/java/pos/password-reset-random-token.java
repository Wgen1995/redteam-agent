// 出处:人工构造(依据 CWE-330/287 Random 弱熵源生成重置令牌)
public String issueToken(String email) {
    String passwordResetToken = String.valueOf(new Random().nextLong());
    tokenStore.put(passwordResetToken, email);
    return passwordResetToken;
}
