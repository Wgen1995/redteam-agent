// 出处:人工构造(依据 CWE-601 登出 returnUrl 直写 Location)
@GetMapping("/logout")
public void logout(@RequestParam String returnUrl, HttpServletResponse response) {
    response.setStatus(HttpServletResponse.SC_FOUND);
    response.addHeader("Location", returnUrl);
    sessionRegistry.expireAll();
}
