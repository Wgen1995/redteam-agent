// 出处:人工构造(依据 CWE-287 验证码无次数上限的改密路径)
@PostMapping("/change-password")
public void change(@RequestBody ChangeRequest req) {
    if (smsGateway.verifyCode(req.phone(), req.code())) {
        accountRepository.setPassword(req.userId(), req.newPassword());
    }
}
