// 出处:人工构造(依据 CWE-94 ScriptEngine 请求参数直达)
ScriptEngine engine = new ScriptEngineManager().getEngineByName("js");
engine.eval(req.getParameter("expr"));
