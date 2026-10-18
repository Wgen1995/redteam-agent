// 出处:人工构造(硬负例:会话属性读取——会话消费非凭据判定)
@GetMapping("/me")
public Profile me(HttpServletRequest request) {
    return (Profile) request.getSession().getAttribute("profile");
}
