// 出处:人工构造(依据 CWE-943 $where 键注入)
const query = { $where: "this.price < " + req.query.cap, status: "active" };
const rows = await db.collection("products").find(query).toArray();
