// 出处: 判定输入请求可写——body 带 role 直入角色判定
public boolean canAccess(User user, Request req) {
  return roleChecker.has(user, req.getParameter("role"));
}
