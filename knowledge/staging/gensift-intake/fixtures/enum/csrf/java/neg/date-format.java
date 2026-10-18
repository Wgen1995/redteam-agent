// 出处:人工构造(硬负例:日期格式化)
public String renderDeadline(ZonedDateTime t) {
    return DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm").format(t);
}
