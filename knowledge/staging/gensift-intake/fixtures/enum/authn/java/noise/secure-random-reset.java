// 出处:人工构造(噪音:SecureRandom 令牌+短时效+一次性)
public String passwordResetToken(String email) {
    String resetToken = new BigInteger(130, new SecureRandom()).toString(32);
    tokenStore.put(resetToken, email, Duration.ofMinutes(15), true);
    return resetToken;
}
