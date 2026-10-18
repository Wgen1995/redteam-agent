// 出处: 系统属性读取硬编码默认（S1 起步集——config-security CS-J06）
public class VaultConfig {
  public String token() {
    return System.getProperty("vault.token", "dev-token-12345");
  }
}
