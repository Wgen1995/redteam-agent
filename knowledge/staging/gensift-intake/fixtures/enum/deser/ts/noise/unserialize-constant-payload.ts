// 出处:人工构造(噪音:服务端自产常量载荷上的读点——允许命中，常量实参由 C1 反证)
const nodeSerialize = require("node-serialize");
const fixed = Buffer.from("rO0ABQ==", "base64").toString("utf8");
const v = nodeSerialize.unserialize(fixed);
