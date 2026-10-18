// 出处: noise——缓存加速权限判定（判定语义不变）
public boolean has(User u, String perm) {
  return cache.get(u.getId() + ":" + perm, k -> roleChecker.check(u, perm));
}
