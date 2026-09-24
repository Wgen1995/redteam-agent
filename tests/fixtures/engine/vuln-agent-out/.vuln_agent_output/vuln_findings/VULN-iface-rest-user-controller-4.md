# 健康检查 - 回连地址猜想（缺 POC 四要素）
**类型**：SSRF
**位置**：HealthController.java:18
**CVSS 评分**：3.7
**严重性**：低
**触发条件**：callback 参数可指定回连地址（未实际发包验证）
**事实依据**：
    // HealthController.java:18 - 回连地址取自请求参数
    HttpClient.get(req.getParameter("callback"));
