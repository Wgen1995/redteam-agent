// 出处: INV-003 读-判-写三段分离（并发兑换可致负余额）
public void spendPoints(String userId, long delta) {
  long balance = pointsRepo.findBalance(userId);
  if (balance >= delta) {
    pointsRepo.update(userId, balance - delta);
  }
}
