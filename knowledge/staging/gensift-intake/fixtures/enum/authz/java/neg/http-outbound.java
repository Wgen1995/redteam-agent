// 出处:人工构造(硬负例:出站拉取公共配置——getForObject 非 .get( 形态)
String body = restClient.getForObject("https://cdn.example.net/app-config.json", String.class);
