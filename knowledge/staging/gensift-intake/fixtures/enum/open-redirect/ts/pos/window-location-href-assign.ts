// 出处:人工构造(依据 CWE-601 客户端 href 赋值跳转)
export function completeOnboarding(returnTo: string) {
  window.location.href = returnTo;
}
