// 出处:人工构造(依据 CWE-601 OAuth 回调 relay 目标可控)
@GetMapping("/oauth/callback")
public RedirectView callback(@RequestParam String state) {
    String relay = oauthService.relayTarget(state);
    return new RedirectView(relay);
}
