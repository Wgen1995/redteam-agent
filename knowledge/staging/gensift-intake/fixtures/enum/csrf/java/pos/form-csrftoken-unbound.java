// 出处:人工构造(依据 CWE-352 token 下发到表单但服务端无比对行)
@GetMapping("/transfer/form")
public String transferForm(Model model) {
    model.addAttribute("csrfToken", tokenGenerator.nextValue());
    return "transfer";
}
