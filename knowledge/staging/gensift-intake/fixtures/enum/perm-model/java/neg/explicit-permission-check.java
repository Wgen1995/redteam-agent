// 出处: 合规形态——显式权限判定（上下文会话取主体）
public boolean canAccess(Session session, String perm) {
  return session.getPermissions().contains(perm);
}
