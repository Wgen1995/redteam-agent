// 出处:人工构造(依据 CWE-601 仅 startsWith("/") 检查,//evil.com 通过)
@PostMapping("/switch-org")
public String switchOrg(@RequestParam String next) {
    if (!next.startsWith("/")) throw new IllegalArgumentException("relative only");
    return "redirect:" + next;
}
