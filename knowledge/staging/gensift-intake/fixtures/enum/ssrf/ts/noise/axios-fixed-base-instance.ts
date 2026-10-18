// 出处:人工构造(噪音:同 API 安全用法——固定 baseURL 实例,允许命中)
const { data } = await axios.create({ baseURL: 'https://api.internal.example' }).get('/users');
return data;
