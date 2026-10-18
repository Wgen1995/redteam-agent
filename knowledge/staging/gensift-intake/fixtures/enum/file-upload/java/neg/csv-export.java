// 出处:人工构造(硬负例:CSV 导出)
java.io.PrintWriter out = resp.getWriter();
for (String[] row : rows) { out.println(String.join(",", row)); }
