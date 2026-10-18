// 出处:人工构造(依据 CWE-400 用户可控正则编译)
Pattern rule = Pattern.compile(ruleService.load(request.getParameter("tenant")));
