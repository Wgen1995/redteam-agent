// 出处:人工构造(噪音:同 API 安全用法——常量 URL,允许命中,由五步判别)
Catalog c = restTemplate.getForObject("https://api.internal.example/catalog/v1", Catalog.class);
return c.getItems();
