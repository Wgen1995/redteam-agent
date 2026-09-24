# 用户导出 - 导出接口越权存疑
**类型**：越权访问
**位置**：UserController.java:120
**CVSS 评分**：5.3
**严重性**：中
**触发条件**：普通用户会话请求全量导出接口
**时间**：2026-09-24T10:31:12+08:00
**环境**：same-host
**raw_request**：
    GET /api/users/export?format=csv HTTP/1.1
    Host: app.intranet
**raw_response**：
    HTTP/1.1 403 Forbidden
    Content-Type: application/json
    {"errorCode": "A1024", "msg": "权限不足"}
**事实依据**：
    信息不足：网关层是否统一鉴权无法从源码确认（SUSPECTED——中间防护层存在性未知）
