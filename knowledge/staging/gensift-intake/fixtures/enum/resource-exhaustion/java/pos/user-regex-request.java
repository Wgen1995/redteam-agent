// 出处:人工构造(依据 CWE-400 request 参数可控正则)
Pattern dynamic = Pattern.compile(request.getParameter("pattern"));
