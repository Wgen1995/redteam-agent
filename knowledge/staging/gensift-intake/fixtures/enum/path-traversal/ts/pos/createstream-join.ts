// 出处:人工构造(依据 CWE-22 Node fs 流读取形态)
const rs = fs.createReadStream(path.join(MEDIA_ROOT, req.query.f));
rs.pipe(res);
