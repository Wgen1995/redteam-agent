// 出处: INV-004 阴性边界——签名报价单授权价格
public Order quoteOrder(SignedQuote quote) {
  quoteVerifier.verify(quote);
  return Order.of(quote.total(), quote.discount());
}
