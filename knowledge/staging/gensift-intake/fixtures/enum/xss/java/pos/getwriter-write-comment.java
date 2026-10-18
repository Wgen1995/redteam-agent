// 出处:人工构造(依据 CWE-79 存储型:评论体回读直出,写入点在别处)
response.getWriter().write(commentBody);
