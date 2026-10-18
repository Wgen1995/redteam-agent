// 出处:人工构造(硬负例:include 固定内部片段)
RequestDispatcher header = request.getRequestDispatcher("/fragments/header.jsp");
header.include(request, response);
