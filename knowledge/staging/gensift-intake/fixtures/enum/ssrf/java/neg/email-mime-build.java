// 出处:人工构造(硬负例:仅构造邮件体,无传输调用)
MimeMessage message = mailSender.createMimeMessage();
MimeMessageHelper helper = new MimeMessageHelper(message);
helper.setTo(recipient);
helper.setSubject("welcome");
helper.setText(templateRendered, true);
