// 出处:人工构造(噪音:同步器 token 服务端会话绑定比对)
@PostMapping("/transfer")
public void transfer(@RequestBody TransferCmd cmd, @RequestParam("_csrf") String submitted, HttpServletRequest request) {
    String expected = (String) request.getSession().getAttribute("csrfToken");
    if (!expected.equals(submitted)) throw new ResponseStatusException(FORBIDDEN);
    transferService.execute(cmd);
}
