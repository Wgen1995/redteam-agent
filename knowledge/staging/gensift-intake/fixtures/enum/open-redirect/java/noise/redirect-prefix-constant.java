// 出处:人工构造(噪音:常量视图名前缀)
@PostMapping("/login")
public String login(@RequestBody Credentials cred) {
    authService.assertValid(cred);
    return "redirect:/dashboard";
}
