// 出处:人工构造(硬负例:缓存响应头写入——头写入易混但非本类目标)
public void applyCachePolicy(HttpServletResponse response) {
    response.setHeader("Cache-Control", "no-store");
    response.setDateHeader("Expires", 0);
}
