// 出处:人工构造(噪音:全属性 Set-Cookie 头直写)
@GetMapping("/sso/landing")
public void landing(@RequestParam String code, HttpServletResponse response) {
    String sessionValue = ssoService.exchange(code);
    response.setHeader("Set-Cookie", "sid=" + sessionValue + "; Path=/; Secure; HttpOnly; SameSite=Strict");
}
