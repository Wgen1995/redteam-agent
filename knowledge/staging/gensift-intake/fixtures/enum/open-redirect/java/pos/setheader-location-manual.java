// 出处:人工构造(依据 CWE-601 手工拼装 30x+Location 直写)
@GetMapping("/go")
public void go(@RequestParam String url, HttpServletResponse response) {
    response.setStatus(HttpServletResponse.SC_MOVED_TEMPORARILY);
    response.setHeader("Location", url);
}
