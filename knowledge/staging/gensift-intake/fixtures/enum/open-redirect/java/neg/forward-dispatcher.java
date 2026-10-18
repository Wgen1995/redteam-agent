// 出处:人工构造(硬负例:服务端 forward 转发,不经浏览器非重定向)
@GetMapping("/legacy/entry")
public void entry(HttpServletRequest request, HttpServletResponse response) throws Exception {
    request.getRequestDispatcher("/home").forward(request, response);
}
