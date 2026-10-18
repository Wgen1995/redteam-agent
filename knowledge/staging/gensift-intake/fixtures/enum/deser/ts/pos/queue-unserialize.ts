// 出处:人工构造(依据消息队列载荷回读形态)
const nodeSerialize = require("node-serialize");
const job = nodeSerialize.unserialize(Buffer.from(msg.content).toString("utf8"));
