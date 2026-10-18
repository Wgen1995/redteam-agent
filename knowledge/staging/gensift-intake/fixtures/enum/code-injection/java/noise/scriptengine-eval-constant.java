// 出处:人工构造(噪音:常量脚本无输入通道——允许命中,由五步判别)
ScriptEngine engine = new ScriptEngineManager().getEngineByName("js");
engine.eval("print(40 + 2)");
