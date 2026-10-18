// 出处:人工构造(硬负例:数组过滤)
export function activeSubscriptions(subs: Subscription[]): Subscription[] {
  return subs.filter((s) => s.status === "active" && s.renewsAt > Date.now());
}
