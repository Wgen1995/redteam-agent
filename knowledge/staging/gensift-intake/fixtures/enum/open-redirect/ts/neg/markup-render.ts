// 出处:人工构造(硬负例:服务端标记渲染,已转义)
export function renderSummary(item: Item): string {
  return `<li>${escapeHtml(item.title)} — ${item.price}</li>`;
}
