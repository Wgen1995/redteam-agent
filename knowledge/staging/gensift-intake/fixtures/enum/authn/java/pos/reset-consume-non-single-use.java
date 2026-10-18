// 出处:人工构造(依据 CWE-287/613 重置令牌用后不焚)
@PostMapping("/reset")
public void reset(@RequestBody ResetRequest req) {
    accountService.resetPassword(req.token(), req.newPassword());
}
