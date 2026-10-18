// 出处:人工构造(依据 CWE-384 URL 携带会话标识——固定注入向量)
@GetMapping("/login")
public String loginPage(@RequestParam(required = false) String sid, Model model) {
    model.addAttribute("sid", sid);
    return "forward:/login;jsessionid=" + sid;
}
