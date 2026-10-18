// 出处:人工构造(硬负例:国际化消息解析)
public String greet(Locale locale, String name) {
    return messageSource.getMessage("welcome", new Object[]{name}, locale);
}
