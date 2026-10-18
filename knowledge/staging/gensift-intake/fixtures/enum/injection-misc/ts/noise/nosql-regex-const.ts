// 出处:人工构造(噪音:服务端自产 $regex——允许命中)
const phones = await db.collection("users").find({ mobile: { $regex: /^1[3-9]\d{9}$/ } }).toArray();
