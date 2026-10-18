// 出处:人工构造(噪音:同 API 安全用法——常量 URL,允许命中)
Document doc = Jsoup.connect("https://example.com/robots.txt").get();
return doc.select("sitemap");
