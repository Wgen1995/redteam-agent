// 出处:人工构造(依据 CWE-798 apiKey 字面)
const paymentOpts = { apiKey: "sk_live_8f3a91d0c7b64e", timeoutMs: 5000 };
stripe.initialize(paymentOpts);
