// 出处: Spring 配置注入弱默认形态（S1 起步集——config-security CS-J01）
@Component
public class TokenConfig {
  @Value("${app.secret:changeme}")
  private String secret;
  public String secret() { return secret; }
}
