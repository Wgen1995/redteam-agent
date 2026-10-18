// 出处:人工构造(噪音:每层键黑名单守卫——允许命中)
function safeMerge(dst: any, src: any) {
  for (const key of Object.keys(src)) {
    if (key === "__proto__" || key === "constructor" || key === "prototype") continue;
    if (isPlainObject(src[key])) safeMerge(dst[key], src[key]); else dst[key] = src[key];
  }
}
