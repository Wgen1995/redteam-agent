// 出处:人工构造(硬负例:固定 URL 常量表用于生成 sitemap,无外发)
private static final List<String> SITEMAP = List.of(
    "https://www.example.com/",
    "https://www.example.com/about",
    "https://www.example.com/contact");
String xml = SITEMAP.stream().map(u -> "<loc>" + u + "</loc>").collect(Collectors.joining());
