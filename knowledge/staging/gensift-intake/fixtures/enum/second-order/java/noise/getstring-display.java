// 出处:人工构造(噪音:结果集回读拼接进问候语——非 SQL sink 语境)
response.getWriter().write("Hello, " + rs.getString("nickname") + "!");
