// 出处:人工构造(硬负例:CORS 固定来源配置,无外发)
CorsConfiguration config = new CorsConfiguration();
config.setAllowedOrigins(List.of("https://app.example.com", "https://admin.example.com"));
config.setAllowedMethods(List.of("GET", "POST"));
