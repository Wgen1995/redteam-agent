// 出处:人工构造(依据 CWE-94 脚本文本拼接)
ScriptEngine engine = manager.getEngineByName("nashorn");
engine.eval("var x = " + jsonExpr + ";");
