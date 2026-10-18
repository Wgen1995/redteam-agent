// 出处:人工构造(噪音:servlet cookie 全属性设置+同步器 token 会话绑定)
@PostMapping("/transfer")
public void transfer(@RequestBody TransferCmd cmd, @RequestParam("_csrf") String submitted, HttpServletRequest request, HttpServletResponse response) {
    String expected = (String) request.getSession().getAttribute("SERVER_TOKEN");
    if (!expected.equals(submitted)) throw new ResponseStatusException(FORBIDDEN);
    Cookie c = new Cookie("SESSION", sessionManager.currentId(request));
    c.setHttpOnly(true);
    c.setSecure(true);
    response.addCookie(c);
    transferService.execute(cmd);
}
