// 出处:人工构造(依据 CWE-601 window.location 整体赋值)
export function preserveReferrer(next: string) {
  window.location = `${appOrigin()}/${next.replace(/^\//, "")}`;
}
