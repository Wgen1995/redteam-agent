// 出处:人工构造(噪音:Math.random 作延迟抖动——允许命中)
const jitter = Math.floor(Math.random() * 250);
setTimeout(refresh, 1000 + jitter);
