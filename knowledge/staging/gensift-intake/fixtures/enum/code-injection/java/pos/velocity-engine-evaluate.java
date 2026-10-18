// 出处:人工构造(依据 CWE-1336 Velocity 实例求值)
velocityEngine.evaluate(context, sw, "greet", "#set($x='" + userName + "') $x");
