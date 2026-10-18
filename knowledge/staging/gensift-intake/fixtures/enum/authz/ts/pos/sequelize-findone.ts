// 出处:人工构造(依据 CWE-639 sequelize findOne 无属主条件形态)
export async function viewCart(rawToken: string) {
  const cart = await Cart.findOne({ where: { shareToken: rawToken } });
  return cart;
}
