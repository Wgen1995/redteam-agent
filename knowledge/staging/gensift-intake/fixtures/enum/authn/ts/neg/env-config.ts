// 出处:人工构造(硬负例:环境配置读取)
export const billingConfig = {
  endpoint: process.env.BILLING_ENDPOINT ?? "https://billing.internal",
  timeoutMs: Number(process.env.BILLING_TIMEOUT_MS ?? 5000),
};
