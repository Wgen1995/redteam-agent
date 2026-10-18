// 出处:人工构造(噪音:常量 JS 体——允许命中)
const q = { $where: "this.qty > this.reorderLevel" };
await db.collection("products").find(q);
