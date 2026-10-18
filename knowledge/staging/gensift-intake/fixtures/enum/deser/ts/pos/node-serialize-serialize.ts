// 出处:人工构造(node-serialize serialize 写出端——配对出现时读端在别处，C6 追跨请求)
import * as nodeSerialize from "node-serialize";
const blob = nodeSerialize.serialize(sessionObj);
