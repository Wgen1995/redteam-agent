<%-- 出处:人工构造(依据 CWE-79 JSP 表达式直出无转义) --%>
<div>hello <%= request.getParameter("name") %></div>
