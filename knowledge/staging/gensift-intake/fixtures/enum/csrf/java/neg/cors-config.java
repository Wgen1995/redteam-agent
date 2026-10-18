// 出处:人工构造(硬负例:CORS 跨域配置——跨源≠跨站伪造)
@Configuration
public class CorsConfig implements WebMvcConfigurer {
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**").allowedOrigins("https://console.example.com").allowedMethods("GET", "POST");
    }
}
