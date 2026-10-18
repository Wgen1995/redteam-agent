// 出处:人工构造(硬负例:固定模板邮件发送,链接为常量)
public void sendWelcome(String email) {
    mailer.send(email, "welcome", Map.of("docs", "https://help.example.com/start"));
}
