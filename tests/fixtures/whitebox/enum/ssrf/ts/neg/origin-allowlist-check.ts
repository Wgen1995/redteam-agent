// 出处:人工构造(硬负例:origin 白名单校验,无外发)
const target = new URL(submittedUrl);
if (target.origin !== 'https://cdn.example.com') { throw new Error('blocked'); }
return target.pathname;
