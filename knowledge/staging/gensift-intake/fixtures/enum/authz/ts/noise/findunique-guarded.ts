// 出处:人工构造(噪音:断言守卫后的 findUnique)
export async function invoice(invoiceId: number, ctx: Context) {
  await assertOwner("invoice", invoiceId, ctx.principal);
  return await prisma.invoice.findUnique({ where: { id: invoiceId } });
}
