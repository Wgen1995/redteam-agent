// 出处:人工构造(硬负例:脚本引擎 eval 属 code-injection 类)
Object r = engine.eval("var x = " + jsonExpr + ";");
