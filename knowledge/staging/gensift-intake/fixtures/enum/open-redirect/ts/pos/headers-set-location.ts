// 出处:人工构造(依据 CWE-601 Response 头直写 Location)
export function manualJump(target: string) {
  const r = new Response(null, { status: 302 });
  r.headers.set("Location", target);
  return r;
}
