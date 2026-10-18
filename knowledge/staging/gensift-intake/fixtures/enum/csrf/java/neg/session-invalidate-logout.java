// 出处:人工构造(硬负例:注销使会话失效——会话生命周期非 cookie 下发形态)
@PostMapping("/logout")
public void logout(HttpServletRequest request) {
    request.getSession().invalidate();
    securityContextLogoutHandler.logout(request, null, null);
}
