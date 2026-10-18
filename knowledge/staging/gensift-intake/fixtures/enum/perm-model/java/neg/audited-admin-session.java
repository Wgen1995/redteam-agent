// 出处: 阴性边界——平台运营侧全租户管理走独立 admin 会话+审计
public List<Tenant> listAll(AdminSession session) {
  auditRepo.append("admin-list-all", session.getOperator());
  return tenantRepo.findAll();
}
