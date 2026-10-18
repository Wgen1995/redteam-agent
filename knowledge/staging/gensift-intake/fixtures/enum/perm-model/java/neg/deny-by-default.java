// 出处: 合规形态——缺省拒绝
public boolean check(Permission p) {
  return granted.contains(p) ? true : false;
}
