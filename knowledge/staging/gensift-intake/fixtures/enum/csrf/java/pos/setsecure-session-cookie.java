// 出处:人工构造(依据 CWE-352 Secure 有而 SameSite 缺席的下发形态)
@PostMapping("/account/lang")
public void switchLanguage(@RequestBody LangChange req, HttpServletResponse response) {
    Cookie c = new Cookie("SESSION", sessionManager.rotate());
    c.setSecure(true);
    response.addCookie(c);
    prefs.apply(req);
}
