// 出处:人工构造(依据 CWE-352 Set-Cookie 头直写 SameSite=None 宽松形态)
@GetMapping("/sso/landing")
public void landing(@RequestParam String code, HttpServletResponse response) {
    String sessionValue = ssoService.exchange(code);
    response.setHeader("Set-Cookie", "sid=" + sessionValue + "; Path=/; SameSite=None");
}
