// 出处: INV-002 合规形态——条件更新一条语句+唯一索引兜底
public boolean redeem(String code) {
  int n = jdbc.update("UPDATE coupon SET used=true WHERE code=? AND used=false", code);
  return n == 1;
}
