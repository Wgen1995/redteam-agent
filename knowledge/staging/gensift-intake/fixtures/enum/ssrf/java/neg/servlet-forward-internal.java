// 出处:人工构造(硬负例:服务端转发到固定内部 JSP)
RequestDispatcher dispatcher = request.getRequestDispatcher("/WEB-INF/views/user.jsp");
dispatcher.forward(request, response);
