// 出处:人工构造(噪音:服务端算好的 discount 仅用于展示——弱锚命中,安全由 ⑥ 判别)
public PromoView view(Order order) {
    Money serverSide = pricingEngine.serverDiscount(order); // 服务端计算
    return new PromoView(formatMoney(serverSide), order.getLines()); // 展示层不参与结算
}
