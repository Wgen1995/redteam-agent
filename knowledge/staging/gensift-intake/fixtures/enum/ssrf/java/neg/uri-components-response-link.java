// 出处:人工构造(硬负例:构造响应里的固定链接,非服务端外发)
String link = UriComponentsBuilder.fromHttpUrl("https://cdn.example.com")
    .pathSegment("img", assetId)
    .queryParam("v", "2")
    .build()
    .toUriString();
response.setHeader("X-Asset-Link", link);
