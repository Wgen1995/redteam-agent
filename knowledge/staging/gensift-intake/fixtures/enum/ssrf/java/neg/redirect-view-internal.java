// 出处:人工构造(硬负例:Spring 视图重定向到固定内部路径)
if (!auth.isAuthenticated()) {
    return "redirect:/login";
}
return "users/profile";
