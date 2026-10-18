// 出处:人工构造(噪音:解析后 host 与固定白名单全等再跳)
private static final Set<String> ALLOWED_HOSTS = Set.of("console.example.com", "docs.example.com");
@GetMapping("/jump")
public void jump(@RequestParam String target, HttpServletResponse response) throws IOException {
    URI uri = URI.create(target);
    if (!ALLOWED_HOSTS.contains(uri.getHost())) throw new ResponseStatusException(FORBIDDEN);
    response.sendRedirect(uri.toString());
}
