// 出处:人工构造(硬负例:CORS 预检响应头处理)
public void handlePreflight(HttpServletRequest req, HttpServletResponse res) {
    res.setHeader("Access-Control-Allow-Origin", "https://console.example.com");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
}
