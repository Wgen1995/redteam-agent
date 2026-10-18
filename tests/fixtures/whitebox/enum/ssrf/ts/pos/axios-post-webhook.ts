// 出处:人工构造(依据 CWE-918 axios webhook 形态)
export async function notify(webhookUrl: string, message: string) {
  await axios.post(webhookUrl, { text: message });
}
