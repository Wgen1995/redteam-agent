// 出处:人工构造(依据 CWE-1321 深拷贝工具封装后键回写)
import { deepCopy } from "../utils/clone";
const merged = deepCopy(defaults);
for (const k of Object.keys(req.body)) {
  merged[k] = deepCopy(req.body[k]);
}
