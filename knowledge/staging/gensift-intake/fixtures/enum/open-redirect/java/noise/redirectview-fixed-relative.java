// 出处:人工构造(噪音:常量相对目标 RedirectView)
@GetMapping("/oauth/error")
public RedirectView oauthError() {
    return new RedirectView("/signin?oauth=failed");
}
