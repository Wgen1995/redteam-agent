// 出处:人工构造(依据 CWE-94 receiver 命名漂移形,家族标记兜)
ScriptEngine se = new ScriptEngineManager().getEngineByName("nashorn");
se.eval(ruleScript);
