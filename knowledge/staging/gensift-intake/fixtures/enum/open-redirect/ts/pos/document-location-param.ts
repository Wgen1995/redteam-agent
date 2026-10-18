// 出处:人工构造(依据 CWE-601 document.location 赋值)
export function legacyJump(target: string) {
  document.location = target;
}
