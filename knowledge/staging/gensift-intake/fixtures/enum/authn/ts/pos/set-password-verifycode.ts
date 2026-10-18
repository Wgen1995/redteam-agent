// 出处:人工构造(依据 CWE-287 验证码校验后改密,无次数上限)
export async function changePassword(userId: string, code: string, next: string) {
  if (await sms.verifyCode(userId, code)) {
    await users.setPassword(userId, next);
  }
}
