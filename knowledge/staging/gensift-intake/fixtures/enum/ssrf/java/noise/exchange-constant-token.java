// 出处:人工构造(噪音:同 API 安全用法——常量 token 端点,允许命中)
ResponseEntity<TokenResponse> re = restTemplate.exchange("https://sso.internal/oauth2/token", HttpMethod.POST, entity, TokenResponse.class);
return re.getBody().getAccessToken();
