// 出处:人工构造(依据 CWE-79 存储型:昵称字段回显)
while (rs.next()) { out.println("<li>" + rs.getString("bio") + "</li>"); }
