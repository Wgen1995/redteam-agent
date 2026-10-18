// 出处:人工构造(噪音:UUID 落盘名——允许命中)
const tmp = path.join(OS_TMP, crypto.randomUUID() + '.part');
await fs.promises.writeFile(tmp, payload);
