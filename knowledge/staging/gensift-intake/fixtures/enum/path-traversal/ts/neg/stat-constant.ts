// 出处:人工构造(硬负例:常量路径元数据)
const st = fs.statSync('/etc/hosts');
return st.isFile();
