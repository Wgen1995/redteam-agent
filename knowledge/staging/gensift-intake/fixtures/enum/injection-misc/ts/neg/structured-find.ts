// 出处:人工构造(硬负例:结构化字段查询)
const rows = await db.collection("users").find({ tenant, status: "active" }).toArray();
