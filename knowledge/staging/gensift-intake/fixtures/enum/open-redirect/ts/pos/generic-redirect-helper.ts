// 出处:人工构造(依据 CWE-601 工具层 reply.redirect 透传)
export function sendTo(reply: { redirect(url: string): void }, target: string) {
  return reply.redirect(target);
}
