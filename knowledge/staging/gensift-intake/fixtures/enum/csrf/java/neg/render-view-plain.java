// 出处:人工构造(硬负例:普通视图名返回,无前缀拼接)
@GetMapping("/welcome")
public String welcome(Model model) {
    model.addAttribute("user", currentUser());
    return "welcome";
}
