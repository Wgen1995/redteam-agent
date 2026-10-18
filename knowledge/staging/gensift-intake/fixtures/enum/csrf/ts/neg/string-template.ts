// 出处:人工构造(硬负例:模板字符串拼装展示文案)
export function invoiceLabel(inv: Invoice): string {
  return `invoice ${inv.number} of ${inv.customerName}`;
}
