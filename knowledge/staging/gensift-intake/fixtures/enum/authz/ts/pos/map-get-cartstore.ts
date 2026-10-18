// 出处:人工构造(依据 CWE-639 内存态按 id 取形态)
export function loadCart(cartId: string) {
  const cart = cartStore.get(cartId);
  return cart ?? emptyCart;
}
