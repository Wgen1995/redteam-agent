// 出处: noise——特性开关与权限判定解耦
public boolean enabled(String flag) {
  return flags.isOn(flag);
}
