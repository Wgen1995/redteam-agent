// 出处:人工构造(硬负例:入口注解无拼接无回读)
public Report report(@RequestParam String name) {
    return reportService.render(name);
}
