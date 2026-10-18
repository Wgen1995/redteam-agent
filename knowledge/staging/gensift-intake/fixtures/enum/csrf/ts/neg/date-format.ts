// 出处:人工构造(硬负例:日期格式化)
export function fmtDeadline(d: Date): string {
  return new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(d);
}
