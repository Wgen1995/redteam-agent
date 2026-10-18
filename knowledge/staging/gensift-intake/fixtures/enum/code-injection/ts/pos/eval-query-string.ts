// 出处:人工构造(依据 CWE-94 请求参数直达 eval)
const r = eval(String(req.query.expr));
