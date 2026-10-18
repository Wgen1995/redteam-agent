// 出处:人工构造(依据 NoSQL 认证绕过形态——$ne 万能密码)
const user = await db.collection("users").findOne({ email: req.body.email, password: { $ne: "" } });
