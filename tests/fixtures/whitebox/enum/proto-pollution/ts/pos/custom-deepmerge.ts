// 出处:人工构造(依据 CWE-1321 自研递归合并无键过滤)
function deepMerge(target: any, source: any) {
  for (const key in source) {
    if (typeof source[key] === "object") {
      target[key] = deepMerge(target[key] ?? {}, source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}
export const merged = deepMerge({}, req.body);
