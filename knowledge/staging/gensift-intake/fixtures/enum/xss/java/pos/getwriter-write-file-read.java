// 出处:人工构造(依据 CWE-79 文件片段内容回显)
response.getWriter().write(new String(Files.readAllBytes(snippetPath)));
