# 段② 攻击面测绘（surface）——加载：intent.kind = surface

单写者铁律：你只产 submissions/<intent-id>/submission.json；一切落账由总控验收后执行。

## 测绘路线（按优先级）
1. **文档与自描述端点**：Swagger/OpenAPI（/swagger、/v2/api-docs、/openapi.json）、
   Spring Actuator（/actuator/*：env/heapdump/mappings 优先）、Druid 监控（/druid/index.html，
   弱口令与未授权两手都要试）、API 网关调试端点。
2. **前端 JS=API 说明书**：全站 JS 拉取入库（artifacts/），grep 未文档化接口/内部域名/
   硬编码密钥形态（只记指纹与位置，真值脱敏）。
3. **认证体系还原**：会话载体（Cookie/JWT/OAuth/SSO）、登录/注册/找回/改密全链路、
   角色枚举（注册页/前端路由守卫/js 权限表）——role 清单回填 creds[] 建议（总控 add-cred）。
4. **直连优先序**：微服务直连>内部工具>网关主 API（绕过网关鉴权是高频攻击面；
   内网域名/端口从 A2/A3 与 JS 挖掘交叉）。

## 落账口径
新端点→assets[] type=endpoint value=host/path meta=protected|public；
认证观察→facts[] kind=authz（如「角色 X 可达端点 Y」）；内部工具→assets[] type=app。
界外资产也报（总控复判）；不铸 ID；不写矩阵。

## 提交纪律
预算内做不完→status=partial 附已完成清单；工具失败换备选路径仍失败→status=blocked 附因。
