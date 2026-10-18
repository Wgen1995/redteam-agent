// 出处: INV-004 预估接口回显（noise——以服务端结算为准的比对形态）
public Draft preview(Cart cart) {
  Draft d = new Draft();
  d.setEstimate(cart.getClientEstimate());
  d.setSettlement(priceService.settle(cart));
  return d;
}
