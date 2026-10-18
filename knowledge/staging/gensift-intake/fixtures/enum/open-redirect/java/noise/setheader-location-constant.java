// 出处:人工构造(噪音:常量 Location)
@GetMapping("/session/expired")
public void expired(HttpServletResponse response) {
    response.setHeader("Location", "/signin?expired=1");
    response.setStatus(HttpServletResponse.SC_MOVED_TEMPORARILY);
}
