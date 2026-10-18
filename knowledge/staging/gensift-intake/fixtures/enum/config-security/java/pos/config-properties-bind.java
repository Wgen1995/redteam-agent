// 出处:Spring 配置绑定类 relaxed binding 散射点（S1 起步集——config-security CS-J03）
@ConfigurationProperties(prefix = "app.admin")
public class AdminProps {
  private String token;
  private Boolean debug;
}
