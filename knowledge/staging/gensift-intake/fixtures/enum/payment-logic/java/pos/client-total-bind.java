// 出处: INV-004 mass assignment 金额直绑形态（S1 判据类起步集）
@PostMapping("/orders")
public Order create(@RequestBody OrderRequest req) {
  Order o = new Order();
  o.setTotal(req.getTotal());
  o.setDiscountedPrice(req.getDiscountedPrice());
  return repo.save(o);
}
