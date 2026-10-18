// 出处:人工构造(硬负例:视图渲染无对象数据访问)
public String list(Model model) {
    model.addAttribute("title", "billing history");
    model.addAttribute("rows", rows);
    return "billing/list";
}
