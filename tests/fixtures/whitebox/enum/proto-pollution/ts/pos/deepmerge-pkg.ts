// 出处:人工构造(依据 deepmerge 包递归合并用户键形态)
import deepmerge from "deepmerge";
const merged = deepmerge(defaults, req.body);
export default merged;
