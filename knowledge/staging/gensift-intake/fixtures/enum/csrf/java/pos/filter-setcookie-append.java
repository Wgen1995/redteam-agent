// 出处:人工构造(依据 CWE-352 过滤器追加 Set-Cookie 无属性形态)
public class DeviceMarkerFilter implements Filter {
    public void doFilter(HttpServletRequest req, HttpServletResponse res, FilterChain chain) throws IOException, ServletException {
        res.addHeader("Set-Cookie", "device=" + req.getParameter("device") + "; Path=/");
        chain.doFilter(req, res);
    }
}
