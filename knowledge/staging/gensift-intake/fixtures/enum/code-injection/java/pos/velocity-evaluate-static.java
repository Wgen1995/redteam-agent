// 出处:人工构造(依据 CWE-1336 Velocity 静态求值)
Velocity.evaluate(context, writer, "user-tpl", request.getParameter("tpl"));
