// 出处: INV-003 合规形态——balance>=delta 条件更新
public void spendPoints(String userId, long delta) {
  jdbc.update("UPDATE points SET balance = balance - ? WHERE user_id = ? AND balance >= ?", delta, userId, delta);
}
