# 出处:人工构造(噪音:同 API 安全用法——类型/大小校验后转私有桶;允许命中)
@app.post('/badge')
async def badge(file: UploadFile = File(...)):
    if file.content_type not in ('image/png', 'image/jpeg'):
        raise HTTPException(415, 'type')
    data = await file.read()
    if len(data) > 2 * 1024 * 1024:
        raise HTTPException(413, 'size')
    key = f'badges/{uuid4().hex}.png'
    await s3.put(BUCKET, key, data)
    return {'key': key}
