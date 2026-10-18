// 出处:人工构造(依据 CWE-601 Referer 头派生跳转——"跳回来源页"实现)
@GetMapping("/back")
public void back(HttpServletRequest request, HttpServletResponse response) throws IOException {
    response.sendRedirect(request.getHeader("Referer"));
}
