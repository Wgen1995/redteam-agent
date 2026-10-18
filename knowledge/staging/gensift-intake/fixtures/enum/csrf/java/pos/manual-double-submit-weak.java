// 出处:人工构造(依据 CWE-352 双提交互等比对无会话侧——C-g 弱档)
@PostMapping("/account/close")
public void closeAccount(@RequestHeader("X-XSRF-TOKEN") String headerToken, HttpServletRequest request) {
    CsrfToken cookieSide = (CsrfToken) request.getAttribute(CsrfToken.class.getName());
    if (!headerToken.equals(cookieSide.getToken())) {
        throw new ResponseStatusException(FORBIDDEN);
    }
    accountService.closeCurrent();
}
