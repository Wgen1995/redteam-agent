// 出处:人工构造(噪音:属主校验后的按 id 删除)
export async function cancel(orderId: string, actor: string) {
  const order = await Order.findByPk(orderId);
  if (order.owner !== actor) { throw new Error("not owner"); }
  await orderRepo.deleteById(orderId);
}
