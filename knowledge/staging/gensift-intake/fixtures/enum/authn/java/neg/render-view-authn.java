// 出处:人工构造(硬负例:登录页视图渲染,无凭据判定)
@GetMapping("/signin")
public String signinPage(Model model, @RequestParam(required = false) String error) {
    model.addAttribute("error", error != null);
    return "signin";
}
