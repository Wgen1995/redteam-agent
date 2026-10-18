// 出处:人工构造(依据 CWE-352 仅 HttpOnly 无 SameSite 属性形态)
@PostMapping("/profile/email")
public void changeEmail(@RequestBody EmailChange req, HttpServletRequest request, HttpServletResponse response) {
    Cookie c = new Cookie("SESSION", sessionManager.refresh(request));
    c.setHttpOnly(true);
    response.addCookie(c);
    profileService.updateEmail(req);
}
