// 出处: CWE-272 通配权限累积提权形态（S1 判据类起步集）
public class PermissionRegistry {
  public void grant(Role role) {
    role.add("resource:*");
  }
}
