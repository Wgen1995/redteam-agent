// 出处:人工构造(依据 CWE-943 $regex 操作符注入)
const filter = { email: { $regex: req.body.pattern, $options: "i" } };
await db.collection("users").find(filter).limit(20);
