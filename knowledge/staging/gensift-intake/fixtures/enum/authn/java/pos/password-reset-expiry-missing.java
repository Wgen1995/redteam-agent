// 出处:人工构造(依据 CWE-613 重置令牌无有效期,发出后永不失效)
public void passwordReset(ResetCommand cmd) {
    String resetToken = cmd.token();
    if (issuedTokens.contains(resetToken)) {
        accountRepository.resetPassword(resetToken, cmd.newPassword());
    }
}
