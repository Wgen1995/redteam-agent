// 出处:人工构造(依据 CWE-1321 __proto__ 直赋形态)
const config: Record<string, unknown> = {};
config["__proto__"] = req.body.proto;
config.isAdmin = req.body.admin;
