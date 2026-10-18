// 出处:人工构造(硬负例:脚本引擎 eval 属代码注入类,非命令注入)
Object r = engine.eval("var x = " + jsonExpr + ";");
