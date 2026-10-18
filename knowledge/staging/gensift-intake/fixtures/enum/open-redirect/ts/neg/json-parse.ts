// 出处:人工构造(硬负例:JSON 解析到类型)
export function parseWebhook(raw: string): WebhookEvent {
  return JSON.parse(raw) as WebhookEvent;
}
