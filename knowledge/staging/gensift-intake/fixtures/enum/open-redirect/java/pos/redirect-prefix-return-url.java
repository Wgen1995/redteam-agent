// 出处:人工构造(依据 CWE-601 视图名前缀拼接)
@PostMapping("/login")
public String login(@RequestBody Credentials cred) {
    String target = authService.callbackTarget(cred);
    return "redirect:" + target;
}
