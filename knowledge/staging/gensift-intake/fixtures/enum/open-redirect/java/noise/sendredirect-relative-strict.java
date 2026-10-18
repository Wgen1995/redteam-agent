// 出处:人工构造(噪音:相对路径强校验,拒 //与反斜杠)
@GetMapping("/next")
public void next(@RequestParam String to, HttpServletResponse response) throws IOException {
    if (!to.startsWith("/") || to.startsWith("//") || to.contains("\\")) throw new ResponseStatusException(BAD_REQUEST);
    response.sendRedirect(to);
}
