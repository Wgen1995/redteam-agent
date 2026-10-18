// 出处:人工构造(硬负例:前端路由内部跳转)
export function goProfile(userId: string) {
  navigate(`/users/${userId}`);
}
