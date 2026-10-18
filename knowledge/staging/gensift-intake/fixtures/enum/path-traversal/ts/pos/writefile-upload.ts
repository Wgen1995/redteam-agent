// 出处:人工构造(依据 CWE-22 上传落盘形态)
await fs.promises.writeFile(path.join(UPLOAD_DIR, req.file.filename), buffer);
