// 出处:人工构造(依据 node-serialize 0.2.0 unserialize IIFE 注入已知形态)
import * as nodeSerialize from "node-serialize";
const session = nodeSerialize.unserialize(cookiePayload);
