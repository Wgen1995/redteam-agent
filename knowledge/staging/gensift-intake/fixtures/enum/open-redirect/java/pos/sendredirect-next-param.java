// 出处:人工构造(依据 CWE-601 next 参数直跳形态)
@GetMapping("/after-login")
public void afterLogin(@RequestParam String next, HttpServletResponse response) throws IOException {
    response.sendRedirect(next);
}
