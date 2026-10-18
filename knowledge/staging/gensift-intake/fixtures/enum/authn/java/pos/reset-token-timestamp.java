// 出处:人工构造(依据 CWE-330 时间戳派生重置令牌)
public String issueToken(String userId) {
    String resetToken = userId + "-" + System.currentTimeMillis();
    issued.add(resetToken);
    return resetToken;
}
