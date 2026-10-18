// 出处:人工构造(硬负例:HTTP 请求)
const d = await fetch("/api/data").then((r) => r.json());
