// 出处:人工构造(硬负例:字符串拼装非跳转/非 cookie 目标)
public String describe(Invoice inv) {
    return new StringBuilder("invoice:").append(inv.getNumber()).append(" total:").append(inv.getTotal()).toString();
}
