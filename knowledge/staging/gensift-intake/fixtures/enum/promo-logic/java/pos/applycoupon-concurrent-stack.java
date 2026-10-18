// 出处:人工构造(依据 CWE-840 叠加裁决分叉,违反 INV-013/INV-002)
@PostMapping("/cart/coupon")
public Cart applyCoupon(@RequestBody CouponDto dto) {
    Cart cart = cartRepository.findById(dto.getCartId()).orElseThrow();
    if (cart.getCoupons() == null) cart.setCoupons(new ArrayList<>());
    cart.getCoupons().add(dto.getCode());          // 不查已用/已叠加,直接入列
    // 前端把折扣算好传回,结算端原样采用——叠加口径无单一裁决点
    return couponService.applyCoupon(cart.getId(), dto.getCode());
}
