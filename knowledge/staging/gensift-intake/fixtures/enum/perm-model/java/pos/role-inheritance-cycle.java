// 出处: RBAC 继承环——低角色累积出 admin
public void buildRoles() {
  manager.inheritsFrom(staff);
  admin.inheritsFrom(manager);
  staff.inheritsFrom(admin);
}
