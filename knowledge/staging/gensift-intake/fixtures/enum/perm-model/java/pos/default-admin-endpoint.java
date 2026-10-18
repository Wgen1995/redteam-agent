// 出处: 默认安装管理端点+默认凭据分支
@RestController
public class AdminConsole {
  @GetMapping("/admin/console")
  public String console() {
    if ("admin".equals(System.getenv("ADMIN_USER"))) { return "ok"; }
    return "default-credentials";
  }
}
