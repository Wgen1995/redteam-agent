# 出处:人工构造(硬负例:SMTP 发信,非 HTTP 外发)
smtp = smtplib.SMTP("smtp.internal:587", timeout=10)
smtp.sendmail(from_addr, [to_addr], body)
