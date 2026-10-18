// 出处:人工构造(依据 CWE-287 密码重置毒化:Host 头直拼链接,PortSwigger 密码重置毒化同型)
@PostMapping("/forgot-password")
public void forgot(@RequestBody EmailRequest req, HttpServletRequest request) {
    String host = request.getHeader("Host");
    String resetToken = tokenStore.issueFor(req.email());
    String link = "https://" + host + "/reset?token=" + resetToken;
    mailer.send(req.email(), "password reset", link);
}
