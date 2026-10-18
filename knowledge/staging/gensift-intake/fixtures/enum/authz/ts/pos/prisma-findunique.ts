// 出处:人工构造(依据 CWE-639 prisma findUnique 唯一键直查形态)
export async function invoice(invoiceId: number) {
  return await prisma.invoice.findUnique({ where: { id: invoiceId } });
}
