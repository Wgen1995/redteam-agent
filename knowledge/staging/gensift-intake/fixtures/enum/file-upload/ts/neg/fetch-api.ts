// 出处:人工构造(硬负例:外发请求)
const resp = await fetch(webhook, { method: 'POST', body: JSON.stringify(event) });
