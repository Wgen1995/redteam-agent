// 出处: Spring @Value 配置注入点（S1 起步集——config-security CS-J01）
@Component
public class FeatureFlags {
  @Value("${feature.limit}")
  private int limit;
}
