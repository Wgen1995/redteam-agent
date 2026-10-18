// 出处:人工构造(噪音:属主列进查询条件)
export async function loadInvoice(invoiceId: number, ownerId: number) {
  return await Invoice.findOne({ where: { id: invoiceId, ownerId } });
}
