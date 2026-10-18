// 出处:人工构造(噪音:同 API 安全用法——常量 well-known URL,允许命中)
https.get('https://example.com/.well-known/security.txt', (res) => res.pipe(process.stdout));
