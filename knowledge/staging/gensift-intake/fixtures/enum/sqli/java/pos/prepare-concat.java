// 出处:人工构造(prepareStatement 即拼接)
conn.prepareStatement("DELETE FROM t WHERE id=" + req.getParameter("id"));
