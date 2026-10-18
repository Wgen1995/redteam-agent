// 出处:人工构造(依据 CWE-601 SSO 出口 relayState 解码直跳)
@GetMapping("/sso/exit")
public void exit(@RequestParam String relayState, HttpServletResponse response) throws IOException {
    response.sendRedirect(idpConfig.decodeTarget(relayState));
}
