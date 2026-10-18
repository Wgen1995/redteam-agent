// 出处: CORS 通配起源（S1 起步集——config-security CS-J07）
@Configuration
public class CorsConfig {
  public WebMvcConfigurer cors() {
    return registry -> registry.addMapping("/**").allowedOrigins("*");
  }
}
