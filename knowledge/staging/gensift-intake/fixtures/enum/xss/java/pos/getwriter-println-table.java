// 出处:人工构造(依据 CWE-79 存储回读字段进表格行)
response.getWriter().println("<td>" + row.get("note") + "</td>");
