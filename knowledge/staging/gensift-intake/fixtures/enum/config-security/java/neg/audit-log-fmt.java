// 出处: 日志格式化（neg）
public class AuditLog {
  public void log(String user, String action) {
    System.out.printf("user= action=", user, action);
  }
}
