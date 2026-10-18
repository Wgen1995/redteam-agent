// 出处:人工构造(硬负例:日期格式化)
public String format(LocalDate d) {
    return d.format(DateTimeFormatter.ISO_LOCAL_DATE);
}
