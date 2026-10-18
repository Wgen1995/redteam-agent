// 出处:人工构造(硬负例:邮件 MimeBodyPart——Multipart 语义非文件上传)
javax.mail.internet.MimeBodyPart part = new javax.mail.internet.MimeBodyPart();
part.setText(body, "UTF-8");
javax.mail.internet.MimeMultipart multipart = new javax.mail.internet.MimeMultipart();
multipart.addBodyPart(part);
