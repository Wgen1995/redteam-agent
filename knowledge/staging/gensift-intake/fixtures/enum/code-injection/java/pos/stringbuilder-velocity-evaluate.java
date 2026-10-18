// 出处:人工构造(依据 CWE-1336 StringBuilder 链尾进模板文本)
StringBuilder tpl = new StringBuilder("#foreach($i in $items)");
tpl.append(request.getParameter("extra"));
velocityEngine.evaluate(ctx, writer, "tag", tpl.toString());
