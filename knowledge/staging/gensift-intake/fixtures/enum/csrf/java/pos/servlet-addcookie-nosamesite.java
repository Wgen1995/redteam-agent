// 出处:人工构造(依据 CWE-352 会话 cookie 无 SameSite 下发形态)
@PostMapping("/cart/checkout")
public Receipt checkout(@RequestBody Cart cart, HttpServletRequest request, HttpServletResponse response) {
    Cookie c = new Cookie("SESSION", sessionManager.currentId(request));
    response.addCookie(c);
    return orderService.place(cart);
}
