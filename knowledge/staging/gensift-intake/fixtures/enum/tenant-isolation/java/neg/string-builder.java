// 出处:人工构造(硬负例:字符串拼接展示)
public String label(Sku s) {
    return new StringBuilder(s.getName()).append(" #").append(s.getCode()).toString();
}
