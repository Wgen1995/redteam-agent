// 出处: 环境变量读取配置（noise——System.getProperty 锚在，默认值经审计来源）
public class RuntimeConfig {
  public String region() {
    return System.getProperty("deploy.region", "cn-north-1");
  }
}
