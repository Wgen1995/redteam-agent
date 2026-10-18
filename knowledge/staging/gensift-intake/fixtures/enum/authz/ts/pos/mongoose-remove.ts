// 出处:人工构造(依据 CWE-639 mongoose 文档 remove 形态)
export async function revoke(sessionId: string) {
  const session = await SessionModel.findById(sessionId);
  await session.remove();
}
