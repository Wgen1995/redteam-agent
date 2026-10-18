// 出处:人工构造(依据 CWE-918 fetch 形态)
export async function proxyAvatar(avatarUrl: string): Promise<Buffer> {
  const res = await fetch(avatarUrl, { redirect: 'follow' });
  return Buffer.from(await res.arrayBuffer());
}
