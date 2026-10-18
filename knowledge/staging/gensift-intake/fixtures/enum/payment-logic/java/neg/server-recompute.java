// 出处: INV-004 合规形态——服务端价格源重算，客户端金额仅对账
public Order create(@RequestBody OrderRequest req) {
  Price price = priceService.resolve(req.getSku(), req.getQty());
  Order o = Order.of(price.total(), price.discount());
  return repo.save(o);
}
